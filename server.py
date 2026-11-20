import asyncio
import logging
import os
import re
import secrets
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import bcrypt
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url, tz_aware=True)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = "HS256"
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
COUPONS = {"AURA10": 0.10}
FREE_SHIP_THRESHOLD = 999
SHIPPING_FEE = 79

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aura")


# ---------- helpers ----------
def now_utc():
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (AttributeError, TypeError, ValueError):
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "type": "access",
               "exp": now_utc() + timedelta(minutes=60 * 24)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "type": "refresh", "exp": now_utc() + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def set_auth_cookies(response: Response, user_id: str, email: str):
    response.set_cookie(key="access_token", value=create_access_token(user_id, email),
                        httponly=True, secure=True, samesite="none", max_age=60 * 60 * 24, path="/")
    response.set_cookie(key="refresh_token", value=create_refresh_token(user_id),
                        httponly=True, secure=True, samesite="none", max_age=604800, path="/")


def sanitize_user(user: dict) -> dict:
    return {"id": str(user["_id"]), "name": user.get("name", ""), "email": user.get("email", ""),
            "role": user.get("role", "customer")}


def serialize_product(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def serialize_order(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc["created_at"] = doc["created_at"].isoformat() if isinstance(doc.get("created_at"), datetime) else doc.get("created_at")
    return doc


def object_id_from_token(payload: dict) -> ObjectId:
    try:
        return ObjectId(payload["sub"])
    except (KeyError, InvalidId, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": object_id_from_token(payload)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_optional_user(request: Request) -> Optional[dict]:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


# ---------- models ----------
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)


class CartItemIn(BaseModel):
    product_id: str
    size: str = "M"
    qty: int = Field(1, ge=1, le=10)


class AddressIn(BaseModel):
    full_name: str = Field(min_length=2)
    phone: str = Field(min_length=10, max_length=15)
    line1: str = Field(min_length=5)
    city: str
    state: str
    pincode: str = Field(min_length=5, max_length=10)


class OrderIn(BaseModel):
    items: List[CartItemIn]
    address: AddressIn
    payment_method: str = "cod"
    coupon: Optional[str] = None


class WishToggleIn(BaseModel):
    product_id: str


# ---------- seed data ----------
def U(pid):
    return f"https://images.unsplash.com/{pid}?q=85&w=800&h=1200&fit=crop&auto=format"


def P(pid):
    return f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=800&h=1200&fit=crop&dpr=1"


CLOTH = ["S", "M", "L", "XL", "XXL"]
ONE = ["ONE SIZE"]


def product(name, category, price, mrp, image, hover, tags=None, sold=40, rating=4.5, reviews=120,
            fabric="Premium cotton blend", desc=""):
    return {
        "name": name, "category": category, "price": price, "mrp": mrp,
        "image": image, "hover": hover or image,
        "sizes": ONE if category == "accessories" else CLOTH,
        "colors": ["Onyx", "Bone", "Olive"],
        "tags": tags or [], "is_new": "new" in (tags or []),
        "sold": sold, "rating": rating, "reviews": reviews,
        "fabric": fabric, "description": desc or f"{name} — cut for the street, finished for the spotlight. Part of the AURA drop.",
        "created_at": now_utc(),
    }


PRODUCTS = [
    product("Midnight Flora Resort Shirt", "shirts", 1499, 1999, U("photo-1536766820879-059fec98ec0a"), U("photo-1626557981101-aae6f84aa6ff"), ["bestseller"], sold=310, rating=4.7, reviews=412),
    product("Cerulean Road Button-Up", "shirts", 1699, 2299, U("photo-1615482572493-6d8be4ce0dc6"), U("photo-1709004915865-38bc70f4cb78"), [], sold=180, rating=4.5, reviews=230),
    product("Dune Safari Overshirt", "shirts", 1899, 2499, U("photo-1709004915865-38bc70f4cb78"), U("photo-1615482572493-6d8be4ce0dc6"), ["new"], sold=95),
    product("Matisse Bloom Relaxed Shirt", "shirts", 1799, 2399, P(2421356), U("photo-1536766820879-059fec98ec0a"), ["new"], sold=120),
    product("Grid Theory Check Shirt", "shirts", 1599, 2099, U("photo-1626557981101-aae6f84aa6ff"), P(2421356), [], sold=150),
    product("Void Blanket Heavy Tee", "tshirts", 999, 1499, U("photo-1553859943-a02c5418b798"), P(19461507), ["bestseller"], sold=520, rating=4.8, reviews=890),
    product("Concrete Mural Graphic Tee", "tshirts", 1099, 1599, U("photo-1571119816306-c0c00469dc2f"), U("photo-1689044611227-3267fabaf76a"), ["new"], sold=140),
    product("Static Bloom Oversized Tee", "tshirts", 1049, 1549, U("photo-1689044611227-3267fabaf76a"), U("photo-1571119816306-c0c00469dc2f"), ["new"], sold=170),
    product("Gallery Poster Boxy Tee", "tshirts", 949, 1349, P(19461507), U("photo-1553859943-a02c5418b798"), [], sold=260),
    product("Court Classic Polo", "polos", 1299, 1799, U("photo-1625910513399-c9fcba54338c"), U("photo-1669791777450-d1ab3816c26d"), [], sold=210),
    product("Studio Ivory Knit Polo", "polos", 1399, 1899, U("photo-1669791777450-d1ab3816c26d"), U("photo-1625910513399-c9fcba54338c"), ["new"], sold=90),
    product("Riviera Club Polo", "polos", 1349, 1849, P(33651005), U("photo-1625910513399-c9fcba54338c"), [], sold=160),
    product("Concrete Menace Denim Jacket", "jackets", 2499, 3299, P(11434887), P(31988321), ["bestseller"], sold=280, rating=4.7, reviews=356),
    product("Downtown Trucker Jacket", "jackets", 2399, 3199, P(31988321), P(11434887), [], sold=190),
    product("Vantablack Leather Jacket", "jackets", 3999, 4999, U("photo-1521223890158-f9f7c3d5d504"), P(1753014), ["bestseller"], sold=240, rating=4.9, reviews=410),
    product("Camel Wool Overcoat", "jackets", 4499, 5499, U("photo-1627637454030-5ddd536e06e5"), U("photo-1516257984-b1b4d707412e"), ["new"], sold=70),
    product("Denim Days Jacket", "jackets", 2699, 3499, U("photo-1516257984-b1b4d707412e"), U("photo-1627637454030-5ddd536e06e5"), [], sold=130),
    product("Brick Layer Moto Jacket", "jackets", 2999, 3799, P(1753014), U("photo-1521223890158-f9f7c3d5d504"), ["new"], sold=110),
    product("Onyx Shadow Cargo", "jeans", 1999, 2699, U("photo-1596766443408-5bf0fd6c0810"), P(31988321), ["new"], sold=150),
    product("Concretewash Slim Jeans", "jeans", 2199, 2899, P(31988321), P(11434887), ["bestseller"], sold=300, rating=4.6, reviews=340),
    product("Indigo Motion Stretch Jeans", "jeans", 2099, 2799, P(11434887), U("photo-1596766443408-5bf0fd6c0810"), [], sold=220),
    product("Tailor Onyx Two-Piece", "trousers", 2999, 3999, U("photo-1618886614638-80e3c103d31a"), U("photo-1617113930975-f9c7243ae527"), ["bestseller"], sold=170, rating=4.8, reviews=290),
    product("Cobalt Statement Blazer", "trousers", 3499, 4499, U("photo-1617137968427-85924c800a22"), U("photo-1617137984095-74e4e5e3613f"), ["new"], sold=85),
    product("Sapphire Slim Suit", "trousers", 3299, 4299, U("photo-1617137984095-74e4e5e3613f"), U("photo-1617137968427-85924c800a22"), [], sold=95),
    product("Midnight Vest Ensemble", "trousers", 2799, 3599, P(33844632), U("photo-1618886614638-80e3c103d31a"), [], sold=105),
    product("Azure Poolside Shorts", "shorts", 999, 1399, U("photo-1740512922260-543b1b83c986"), U("photo-1719087392186-77079650a2bf"), ["new"], sold=140),
    product("Monsoon Street Cargo Shorts", "shorts", 1099, 1499, U("photo-1719087392186-77079650a2bf"), U("photo-1793083873431-24bcd8769e02"), [], sold=160),
    product("Stripe Deck Walking Shorts", "shorts", 1049, 1449, U("photo-1793083873431-24bcd8769e02"), P(4983916), [], sold=120),
    product("Transit Off-White Set", "shorts", 1249, 1699, P(4983916), U("photo-1740512922260-543b1b83c986"), ["new"], sold=100),
    product("Metropolitan Hoodie", "hoodies", 1699, 2299, U("photo-1685328403732-64be6bb9d112"), U("photo-1564557287817-3785e38ec1f5"), ["bestseller"], sold=340, rating=4.8, reviews=560),
    product("Cobalt Signal Hoodie", "hoodies", 1599, 2199, U("photo-1728394604722-c1007e3edf09"), U("photo-1578768079052-aa76e52ff62e"), [], sold=180),
    product("Ashen Concrete Hoodie", "hoodies", 1749, 2399, U("photo-1564557287817-3785e38ec1f5"), U("photo-1685328403732-64be6bb9d112"), ["new"], sold=130),
    product("Sienna Heavyweight Hoodie", "hoodies", 1849, 2499, U("photo-1578768079052-aa76e52ff62e"), U("photo-1728394604722-c1007e3edf09"), ["new"], sold=115),
    product("Tandem Overshirt Co-ord", "coords", 2299, 2999, P(37811695), P(20340057), ["new"], sold=125),
    product("Noir Chronograph", "accessories", 1999, 2599, P(9011184), P(1541495532687), ["bestseller"], sold=200, rating=4.7, reviews=250),
    product("Heritage Wire Watch", "accessories", 1499, 1999, P(1541495532687), P(1629139033414), [], sold=150),
    product("Slate Leather Wallet + Frame Set", "accessories", 1299, 1799, P(1629139033414), P(9011184), ["new"], sold=90),
]

INDEXES = {
    "users": [IndexModel([("email", ASCENDING)], name="email_unique", unique=True)],
    "login_attempts": [IndexModel([("identifier", ASCENDING)], name="identifier")],
    "password_reset_tokens": [IndexModel([("expires_at", ASCENDING)], name="expires_at", expireAfterSeconds=0)],
    "products": [
        IndexModel([("category", ASCENDING)], name="category"),
        IndexModel([("is_new", DESCENDING), ("_id", DESCENDING)], name="new_arrivals"),
        IndexModel([("sold", DESCENDING)], name="popular"),
        IndexModel([("price", ASCENDING)], name="price_asc"),
    ],
    "orders": [IndexModel([("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_recent")],
    "wishlist": [IndexModel([("user_id", ASCENDING)], name="user_id")],
}


async def ensure_indexes():
    for collection, models in INDEXES.items():
        for model in models:
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)


async def seed_products():
    if await db.products.count_documents({}) == 0:
        await db.products.insert_many([dict(p) for p in PRODUCTS])
        logger.info("Seeded %d products", len(PRODUCTS))


async def seed_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    if not admin_email or not admin_password:
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be configured")
    if await db.users.find_one({"email": admin_email}) is None:
        await db.users.insert_one({
            "name": "Admin", "email": admin_email, "password_hash": hash_password(admin_password),
            "role": "admin", "created_at": now_utc(),
        })
        logger.info("Seeded admin user %s", admin_email)


# ---------- app ----------
app = FastAPI(title="AURA API")
api_router = APIRouter(prefix="/api")

origins = [FRONTEND_URL, "http://localhost:3000", "http://localhost:8001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@api_router.get("/")
async def root():
    return {"message": "AURA API live"}


# ---------- auth ----------
@api_router.post("/auth/register")
async def register(input: UserCreate, response: Response):
    email = input.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    doc = {"name": input.name.strip(), "email": email, "password_hash": hash_password(input.password),
           "role": "customer", "created_at": now_utc()}
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    set_auth_cookies(response, user_id, email)
    return {"id": user_id, "name": doc["name"], "email": email, "role": doc["role"]}


@api_router.post("/auth/login")
async def login(input: UserLogin, request: Request, response: Response):
    email = input.email.lower()
    ip = request.client.host if request.client else "unknown"
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier})
    if attempt and attempt.get("locked_until") and attempt["locked_until"] > now_utc():
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in 15 minutes.")
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(input.password, user.get("password_hash", "")):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"updated_at": now_utc(),
             "locked_until": now_utc() + timedelta(minutes=15) if attempt and attempt.get("count", 0) + 1 >= 5 else None}},
            upsert=True)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await db.login_attempts.delete_one({"identifier": identifier})
    set_auth_cookies(response, str(user["_id"]), email)
    return sanitize_user(user)


@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return sanitize_user(user)


@api_router.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": object_id_from_token(payload)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        set_auth_cookies(response, str(user["_id"]), user["email"])
        return {"ok": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@api_router.post("/auth/forgot-password")
async def forgot_password(input: ForgotIn):
    raise HTTPException(
        status_code=501,
        detail="Password reset email delivery is not configured",
    )


@api_router.post("/auth/reset-password")
async def reset_password(input: ResetIn):
    doc = await db.password_reset_tokens.find_one({"token": input.token, "used": False})
    if not doc or doc["expires_at"] < now_utc():
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")
    await db.users.update_one({"email": doc["email"]}, {"$set": {"password_hash": hash_password(input.new_password)}})
    await db.password_reset_tokens.update_one({"token": input.token}, {"$set": {"used": True}})
    return {"ok": True}


# ---------- products ----------
@api_router.get("/products")
async def list_products(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    ids: Optional[str] = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=48),
):
    query = {}
    if category and category != "all":
        query["category"] = category
    if tag:
        query["tags"] = tag
    if q:
        search_pattern = re.escape(q)
        query["$or"] = [
            {"name": {"$regex": search_pattern, "$options": "i"}},
            {"category": {"$regex": search_pattern, "$options": "i"}},
        ]
    if ids:
        try:
            query["_id"] = {"$in": [ObjectId(x) for x in ids.split(",") if x]}
        except (InvalidId, TypeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid product id") from exc
    sort_map = {
        "newest": [("is_new", DESCENDING), ("_id", DESCENDING)],
        "price_asc": [("price", ASCENDING)],
        "price_desc": [("price", DESCENDING)],
        "popular": [("sold", DESCENDING)],
    }
    if sort not in sort_map:
        raise HTTPException(status_code=400, detail="Unsupported product sort")
    total = await db.products.count_documents(query)
    cursor = db.products.find(query).sort(sort_map.get(sort, sort_map["newest"])).skip((page - 1) * limit).limit(limit)
    items = [serialize_product(d) async for d in cursor]
    return {"items": items, "total": total}


@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    try:
        doc = await db.products.find_one({"_id": ObjectId(product_id)})
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=404, detail="Product not found") from exc
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_product(doc)


@api_router.get("/products/{product_id}/related")
async def related_products(product_id: str, limit: int = Query(4, ge=1, le=8)):
    try:
        doc = await db.products.find_one({"_id": ObjectId(product_id)})
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=404, detail="Product not found") from exc
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    cursor = db.products.find({"category": doc["category"], "_id": {"$ne": doc["_id"]}}).limit(limit)
    return [serialize_product(d) async for d in cursor]


# ---------- wishlist ----------
@api_router.get("/wishlist")
async def get_wishlist(user: dict = Depends(get_current_user)):
    doc = await db.wishlist.find_one({"user_id": user["_id"]})
    ids = doc.get("product_ids", []) if doc else []
    if not ids:
        return []
    cursor = db.products.find({"_id": {"$in": ids}})
    items = [serialize_product(d) async for d in cursor]
    items.sort(key=lambda p: ids.index(ObjectId(p["id"])))
    return items


@api_router.post("/wishlist/toggle")
async def toggle_wishlist(input: WishToggleIn, user: dict = Depends(get_current_user)):
    try:
        pid = ObjectId(input.product_id)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid product id") from exc
    doc = await db.wishlist.find_one({"user_id": user["_id"]})
    ids = doc.get("product_ids", []) if doc else []
    ids = [i for i in ids if i != pid] if pid in ids else ids + [pid]
    await db.wishlist.update_one({"user_id": user["_id"]}, {"$set": {"product_ids": ids}}, upsert=True)
    return {"ids": [str(i) for i in ids]}


# ---------- orders ----------
@api_router.post("/orders")
async def create_order(input: OrderIn, user: Optional[dict] = Depends(get_optional_user)):
    if not input.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    line_items, subtotal = [], 0
    for item in input.items:
        try:
            prod = await db.products.find_one({"_id": ObjectId(item.product_id)})
        except (InvalidId, TypeError) as exc:
            raise HTTPException(status_code=400, detail="Unknown product") from exc
        if not prod:
            raise HTTPException(status_code=400, detail="Unknown product")
        line_total = prod["price"] * item.qty
        subtotal += line_total
        line_items.append({"product_id": str(prod["_id"]), "name": prod["name"], "size": item.size,
                           "qty": item.qty, "price": prod["price"], "image": prod["image"]})
    if input.payment_method != "cod":
        raise HTTPException(status_code=400, detail="Only cash on delivery is currently supported")
    if input.coupon and input.coupon not in COUPONS:
        raise HTTPException(status_code=400, detail="Invalid coupon code")
    discount = int(subtotal * COUPONS[input.coupon]) if input.coupon else 0
    shipping = 0 if subtotal - discount >= FREE_SHIP_THRESHOLD else SHIPPING_FEE
    total = subtotal - discount + shipping
    order_no = "AURA-" + secrets.token_hex(3).upper()
    doc = {"order_no": order_no, "user_id": user["_id"] if user else None,
           "email": user.get("email") if user else None,
           "items": line_items, "address": input.address.model_dump(),
           "payment_method": input.payment_method, "subtotal": subtotal, "discount": discount,
           "coupon": input.coupon if discount else None, "shipping": shipping, "total": total,
           "status": "confirmed", "created_at": now_utc(), "eta_days": 7}
    result = await db.orders.insert_one(doc)
    return {**serialize_order(doc), "id": str(result.inserted_id)}


@api_router.get("/orders")
async def list_orders(user: dict = Depends(get_current_user)):
    cursor = db.orders.find({"user_id": user["_id"]}).sort("created_at", DESCENDING).limit(50)
    return [serialize_order(d) async for d in cursor]


@app.on_event("startup")
async def startup():
    app.state.index_task = asyncio.create_task(ensure_indexes())
    await seed_products()
    await seed_admin()


@app.on_event("shutdown")
async def shutdown():
    with suppress(asyncio.CancelledError):
        app.state.index_task.cancel()
        await app.state.index_task
    client.close()


app.include_router(api_router)
