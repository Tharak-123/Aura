import { useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Heart,
  Instagram,
  Menu,
  Search,
  ShoppingBag,
  X,
} from "lucide-react";
import { HashRouter, Route, Routes } from "react-router-dom";
import "@/App.css";

const products = [
  {
    id: 1,
    name: "Everyday Heavyweight Tee",
    category: "Men",
    type: "T-shirts",
    price: 899,
    oldPrice: 1199,
    label: "BESTSELLER",
    image:
      "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 2,
    name: "Soft Ribbed Tank",
    category: "Women",
    type: "T-shirts",
    price: 749,
    label: "JUST IN",
    image:
      "https://images.unsplash.com/photo-1551163943-3f6a855d1153?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 3,
    name: "Textured Weekend Polo",
    category: "Men",
    type: "Sweaters",
    price: 1499,
    image:
      "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 4,
    name: "Relaxed Wide-Leg Trouser",
    category: "Women",
    type: "Trousers",
    price: 1799,
    oldPrice: 2199,
    label: "SALE",
    image:
      "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 5,
    name: "City Utility Overshirt",
    category: "Men",
    type: "Shirts",
    price: 2299,
    label: "JUST IN",
    image:
      "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 6,
    name: "The Daily Carry Tote",
    category: "Accessories",
    type: "Bags",
    price: 999,
    image:
      "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 7,
    name: "Draped Cotton Shirt",
    category: "Women",
    type: "Shirts",
    price: 1599,
    label: "JUST IN",
    image:
      "https://images.unsplash.com/photo-1598554747436-c9293d6a588f?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 8,
    name: "Everyday Canvas Cap",
    category: "Accessories",
    type: "Accessories",
    price: 699,
    oldPrice: 899,
    label: "SALE",
    image:
      "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 9,
    name: "Easy Pace Jogger",
    category: "Men",
    type: "Joggers",
    price: 1599,
    image:
      "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 10,
    name: "Weekend Drawstring Short",
    category: "Men",
    type: "Shorts",
    price: 999,
    image:
      "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 11,
    name: "Cloud Soft Hoodie",
    category: "Women",
    type: "Sweatshirts & Hoodies",
    price: 1899,
    label: "JUST IN",
    image:
      "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=900&q=85",
  },
  {
    id: 12,
    name: "Sunday Knit Sweater",
    category: "Women",
    type: "Sweaters",
    price: 1999,
    oldPrice: 2499,
    label: "SALE",
    image:
      "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=900&q=85",
  },
];

const productTypes = [
  "T-shirts",
  "Shirts",
  "Joggers",
  "Shorts",
  "Trousers",
  "Sweatshirts & Hoodies",
  "Sweaters",
  "Bags",
  "Accessories",
];

const categories = [
  {
    title: "For him",
    subtitle: "Easy layers, all day",
    filter: "Men",
    image:
      "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=1100&q=85",
  },
  {
    title: "For her",
    subtitle: "Everyday, elevated",
    filter: "Women",
    image:
      "https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?auto=format&fit=crop&w=1100&q=85",
  },
  {
    title: "The extras",
    subtitle: "Little things, big energy",
    filter: "Accessories",
    image:
      "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=1100&q=85",
  },
];

const navigation = [
  { label: "New in", filter: "All" },
  { label: "Men", filter: "Men" },
  { label: "Women", filter: "Women" },
  { label: "Accessories", filter: "Accessories" },
  { label: "Sale", filter: "Sale" },
];

const price = (amount) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);

function Storefront() {
  const [activeFilter, setActiveFilter] = useState("All");
  const [activeType, setActiveType] = useState("All");
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);
  const [cart, setCart] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [subscribed, setSubscribed] = useState(false);
  const [checkoutMessage, setCheckoutMessage] = useState("");

  const filteredProducts = products.filter((product) => {
    const matchesFilter =
      activeFilter === "All" ||
      (activeFilter === "Sale" ? product.oldPrice : product.category === activeFilter);
    const matchesType = activeType === "All" || product.type === activeType;
    const matchesSearch = product.name
      .toLowerCase()
      .includes(searchTerm.trim().toLowerCase());

    return matchesFilter && matchesType && matchesSearch;
  });

  const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
  const cartTotal = cart.reduce(
    (total, item) => total + item.price * item.quantity,
    0,
  );

  const showProducts = (filter) => {
    setActiveFilter(filter);
    setActiveType("All");
    setMobileMenuOpen(false);
    document.getElementById("new-arrivals")?.scrollIntoView({ behavior: "smooth" });
  };

  const addToCart = (product) => {
    setCart((currentCart) => {
      const existingItem = currentCart.find((item) => item.id === product.id);

      if (existingItem) {
        return currentCart.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        );
      }

      return [...currentCart, { ...product, quantity: 1 }];
    });
    setCheckoutMessage("");
  };

  const toggleFavorite = (productId) => {
    setFavorites((currentFavorites) =>
      currentFavorites.includes(productId)
        ? currentFavorites.filter((id) => id !== productId)
        : [...currentFavorites, productId],
    );
  };

  const removeFromCart = (productId) => {
    setCart((currentCart) =>
      currentCart.filter((item) => item.id !== productId),
    );
  };

  return (
    <div className="storefront" id="top">
      <div className="announcement">
        <span>Good things, delivered free over ₹1,999</span>
        <a href="#new-arrivals">
          Find your next favourite <ArrowRight size={13} aria-hidden="true" />
        </a>
      </div>

      <header className="site-header">
        <button
          className="icon-button mobile-menu-toggle"
          type="button"
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>

        <a className="wordmark" href="#top" aria-label="AURA Fashion home">
          AURA<span>.</span>
        </a>

        <nav
          className={`main-nav${mobileMenuOpen ? " is-open" : ""}`}
          aria-label="Main navigation"
        >
          {navigation.map((item) => (
            <button
              className={activeFilter === item.filter ? "nav-link is-active" : "nav-link"}
              key={item.label}
              type="button"
              onClick={() => showProducts(item.filter)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="header-actions">
          <button
            className={`icon-button${searchOpen ? " is-active" : ""}`}
            type="button"
            aria-label={searchOpen ? "Close search" : "Search products"}
            onClick={() => {
              setSearchOpen(!searchOpen);
              setSearchTerm("");
            }}
          >
            {searchOpen ? <X size={20} /> : <Search size={20} />}
          </button>
          <button
            className="icon-button bag-button"
            type="button"
            aria-label={`Shopping bag, ${cartCount} items`}
            onClick={() => setCartOpen(true)}
          >
            <ShoppingBag size={20} />
            <span className="bag-count">{cartCount}</span>
          </button>
        </div>
      </header>

      {searchOpen && (
        <form
          className="search-bar"
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            showProducts("All");
          }}
        >
          <Search size={19} aria-hidden="true" />
          <input
            autoFocus
            aria-label="Search products"
            placeholder="Search tees, shirts, accessories..."
            value={searchTerm}
            onChange={(event) => {
              setSearchTerm(event.target.value);
              setActiveFilter("All");
            }}
          />
          <span>{filteredProducts.length} pieces</span>
        </form>
      )}

      <main>
        <section className="hero-section" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow"><span /> THE EVERYDAY EDIT — 01</p>
            <h1 id="hero-title">
              A little
              <br />
              more <em>you.</em>
            </h1>
            <p className="hero-description">
              Thoughtful pieces for wherever the day takes you. Made to wear
              your way, on repeat.
            </p>
            <button
              className="button button-dark"
              type="button"
              onClick={() => showProducts("All")}
            >
              Explore the edit <ArrowRight size={16} aria-hidden="true" />
            </button>
            <div className="hero-note">
              <span className="hero-note-line" />
              <span>New season. Same good feeling.</span>
            </div>
          </div>
          <div className="hero-visual">
            <img
              src="https://images.unsplash.com/photo-1539109136881-3be0616acf4b?auto=format&fit=crop&w=1600&q=90"
              alt="AURA seasonal fashion editorial"
            />
            <div className="hero-sticker">
              <span>STYLE</span>
              <span>IS A</span>
              <strong>FEELING</strong>
            </div>
            <div className="hero-caption">
              <span>THE NEW MOOD</span>
              <span>01 / 04</span>
            </div>
          </div>
        </section>

        <section className="category-section section-wrap" aria-labelledby="category-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">A GOOD PLACE TO START</p>
              <h2 id="category-title">Find your kind of <em>everyday.</em></h2>
            </div>
            <button
              className="text-link"
              type="button"
              onClick={() => showProducts("All")}
            >
              Shop everything <ArrowUpRight size={16} aria-hidden="true" />
            </button>
          </div>
          <div className="category-grid">
            {categories.map((category, index) => (
              <button
                className={`category-card category-card-${index + 1}`}
                key={category.title}
                type="button"
                onClick={() => showProducts(category.filter)}
              >
                <img src={category.image} alt="" loading="lazy" />
                <span className="category-shade" />
                <span className="category-copy">
                  <span>{category.subtitle}</span>
                  <strong>{category.title}</strong>
                </span>
                <span className="category-arrow" aria-hidden="true">
                  <ArrowUpRight size={19} />
                </span>
              </button>
            ))}
          </div>
        </section>

        <section
          className="products-section section-wrap"
          id="new-arrivals"
          aria-labelledby="products-title"
        >
          <div className="section-heading products-heading">
            <div>
              <p className="eyebrow">FRESH FROM THE STUDIO</p>
              <h2 id="products-title">
                {activeType !== "All"
                  ? activeType
                  : activeFilter === "All"
                    ? "New arrivals"
                    : `${activeFilter} edit`}
              </h2>
            </div>
            <div className="filter-tabs" aria-label="Filter products">
              {["All", "Men", "Women", "Accessories", "Sale"].map((filter) => (
                <button
                  className={activeFilter === filter ? "filter-tab is-active" : "filter-tab"}
                  key={filter}
                  type="button"
                  aria-pressed={activeFilter === filter}
                  onClick={() => {
                    setActiveFilter(filter);
                    setActiveType("All");
                  }}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          <div className="type-filter-row" aria-label="Filter by product type">
            <button
              className={activeType === "All" ? "type-filter is-active" : "type-filter"}
              type="button"
              aria-pressed={activeType === "All"}
              onClick={() => setActiveType("All")}
            >
              All pieces
            </button>
            {productTypes.map((type) => (
              <button
                className={activeType === type ? "type-filter is-active" : "type-filter"}
                key={type}
                type="button"
                aria-pressed={activeType === type}
                onClick={() => {
                  setActiveFilter("All");
                  setActiveType(type);
                }}
              >
                {type}
              </button>
            ))}
          </div>

          {filteredProducts.length > 0 ? (
            <div className="product-grid">
              {filteredProducts.map((product) => (
                <article className="product-card" key={product.id}>
                  <div className="product-image-wrap">
                    <img
                      className="product-image"
                      src={product.image}
                      alt={product.name}
                      loading="lazy"
                    />
                    {product.label && (
                      <span className="product-label">{product.label}</span>
                    )}
                    <button
                      className={`favorite-button${favorites.includes(product.id) ? " is-favorite" : ""}`}
                      type="button"
                      aria-label={
                        favorites.includes(product.id)
                          ? `Remove ${product.name} from wishlist`
                          : `Add ${product.name} to wishlist`
                      }
                      onClick={() => toggleFavorite(product.id)}
                    >
                      <Heart
                        size={18}
                        fill={favorites.includes(product.id) ? "currentColor" : "none"}
                      />
                    </button>
                    <button
                      className="quick-add"
                      type="button"
                      onClick={() => addToCart(product)}
                    >
                      Add to bag <span>+</span>
                    </button>
                  </div>
                  <div className="product-details">
                    <div>
                      <p className="product-category">{product.category}</p>
                      <h3>{product.name}</h3>
                    </div>
                    <div className="product-prices">
                      <span>{price(product.price)}</span>
                      {product.oldPrice && (
                        <del>{price(product.oldPrice)}</del>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-search">
              <p>No pieces found for “{searchTerm}”.</p>
              <button
                className="text-link"
                type="button"
                onClick={() => {
                  setSearchTerm("");
                  setActiveFilter("All");
                }}
              >
                Clear search <ArrowRight size={15} />
              </button>
            </div>
          )}
        </section>

        <section className="editorial-section" aria-labelledby="editorial-title">
          <div className="editorial-image">
            <img
              src="https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=1500&q=85"
              alt="A relaxed, layered AURA look"
              loading="lazy"
            />
            <span className="editorial-image-note">AURA / FIELD NOTES / 01</span>
          </div>
          <div className="editorial-copy">
            <p className="eyebrow">A NOTE ON GETTING DRESSED</p>
            <h2 id="editorial-title">
              Keep it
              <br />
              <em>uncomplicated.</em>
            </h2>
            <p>
              The best outfits don't ask for much. A good layer, a familiar
              favourite, and room to make it your own.
            </p>
            <button
              className="text-link"
              type="button"
              onClick={() => showProducts("All")}
            >
              Meet the collection <ArrowRight size={16} aria-hidden="true" />
            </button>
            <span className="editorial-mark">A.</span>
          </div>
        </section>

        <section className="newsletter-section" aria-labelledby="newsletter-title">
          <p className="eyebrow">NOTES FROM AURA</p>
          <h2 id="newsletter-title">A good thing in your <em>inbox.</em></h2>
          <p>New drops, thoughtful edits, and a little inspiration.</p>
          {subscribed ? (
            <div className="subscribe-success" role="status">
              You're on the list. Keep an eye on your inbox.
            </div>
          ) : (
            <form
              className="newsletter-form"
              onSubmit={(event) => {
                event.preventDefault();
                setSubscribed(true);
              }}
            >
              <label className="visually-hidden" htmlFor="newsletter-email">
                Email address
              </label>
              <input
                id="newsletter-email"
                type="email"
                placeholder="Your email address"
                required
              />
              <button type="submit" aria-label="Subscribe to the newsletter">
                <ArrowRight size={19} />
              </button>
            </form>
          )}
          <span className="newsletter-footnote">Just the good stuff. Unsubscribe anytime.</span>
        </section>
      </main>

      <footer className="site-footer" id="about">
        <div className="footer-main">
          <div className="footer-brand">
            <a className="wordmark footer-wordmark" href="#top">
              AURA<span>.</span>
            </a>
            <p>Everyday pieces. A little more feeling.</p>
            <a
              className="social-link"
              href="https://www.instagram.com/"
              target="_blank"
              rel="noreferrer"
              aria-label="Instagram"
            >
              <Instagram size={18} />
            </a>
          </div>
          <div className="footer-links">
            <div>
              <h3>Explore</h3>
              <button type="button" onClick={() => showProducts("All")}>New in</button>
              <button type="button" onClick={() => showProducts("Men")}>Men</button>
              <button type="button" onClick={() => showProducts("Women")}>Women</button>
              <button type="button" onClick={() => showProducts("Accessories")}>Accessories</button>
            </div>
            <div>
              <h3>Need a hand?</h3>
              <a href="mailto:hello@aurafashion.example">Contact us</a>
              <a href="#about">Shipping & returns</a>
              <a href="#about">FAQs</a>
              <a href="#about">Privacy policy</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2026 AURA Fashion. Made for everyday.</span>
          <span>India · INR ₹</span>
        </div>
      </footer>

      {cartOpen && (
        <div
          className="drawer-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setCartOpen(false);
          }}
        >
          <aside className="cart-drawer" role="dialog" aria-modal="true" aria-labelledby="cart-title">
            <div className="drawer-header">
              <div>
                <p className="eyebrow">YOUR GOOD FINDS</p>
                <h2 id="cart-title">Your bag <span>({cartCount})</span></h2>
              </div>
              <button
                className="icon-button"
                type="button"
                aria-label="Close shopping bag"
                onClick={() => setCartOpen(false)}
              >
                <X size={21} />
              </button>
            </div>
            {cart.length === 0 ? (
              <div className="cart-empty">
                <ShoppingBag size={30} strokeWidth={1.3} />
                <p>Your bag is taking a little breather.</p>
                <button
                  className="button button-dark"
                  type="button"
                  onClick={() => setCartOpen(false)}
                >
                  Find something good <ArrowRight size={15} />
                </button>
              </div>
            ) : (
              <>
                <div className="cart-items">
                  {cart.map((item) => (
                    <div className="cart-item" key={item.id}>
                      <img src={item.image} alt="" />
                      <div className="cart-item-info">
                        <span className="product-category">{item.category}</span>
                        <h3>{item.name}</h3>
                        <span>Qty {item.quantity}</span>
                        <button
                          className="remove-item"
                          type="button"
                          onClick={() => removeFromCart(item.id)}
                        >
                          Remove
                        </button>
                      </div>
                      <strong>{price(item.price * item.quantity)}</strong>
                    </div>
                  ))}
                </div>
                <div className="cart-summary">
                  <div><span>Subtotal</span><strong>{price(cartTotal)}</strong></div>
                  <p>Shipping is calculated at checkout.</p>
                  {checkoutMessage && (
                    <p className="checkout-message" role="status">{checkoutMessage}</p>
                  )}
                  <button
                    className="button button-dark checkout-button"
                    type="button"
                    onClick={() =>
                      setCheckoutMessage("Demo checkout only — no payment was taken.")
                    }
                  >
                    Continue to checkout <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="*" element={<Storefront />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
