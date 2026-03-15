import streamlit as st
import pandas as pd
import pyttsx3
import threading
from scraper import scrape_products
from serpapi_scraper import scrape_serpapi, scrape_product_reviews
from database import register_seller, add_product, login_seller, get_seller_products, get_competing_sellers, load_db, REVIEWS_BY_RATING, remove_product
from sentiment_model import analyze_reviews, is_model_ready

# ── Helpers ───────────────────────────────────────────────────────────────────
PRODUCT_ICONS = {"laptop": "💻", "phone": "📱", "tablet": "📟", "mobile": "📱", "computer": "🖥️"}

def speak(text):
    """Speak text in a background thread so Streamlit doesn't freeze."""
    def _run():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            st.session_state["speaking"] = False
        except Exception as e:
            print(f"Voice error: {e}")
            st.session_state["speaking"] = False
    st.session_state["speaking"] = True
    t = threading.Thread(target=_run, daemon=True)
    st.session_state["voice_thread"] = t
    t.start()

def stop_speaking():
    """Stop the voice engine."""
    try:
        engine = pyttsx3.init()
        engine.stop()
    except:
        pass
    st.session_state["speaking"] = False

def get_icon(name):
    for key, icon in PRODUCT_ICONS.items():
        if key in name.lower():
            return icon
    return "📦"

def get_all_competitor_reviews(competitors):
    all_reviews = []
    for c in competitors:
        all_reviews.extend(c.get("review_texts", []))
    return all_reviews

def generate_alerts(your_price, your_rating, your_reviews, your_score, competitors, avg_price):
    """Generate urgent alerts for the seller."""
    alerts = []
    if not competitors:
        return alerts
    cheapest   = min(competitors, key=lambda x: x["price"])
    best_rated = max(competitors, key=lambda x: x["rating"])
    avg_comp_rating = sum(c["rating"] for c in competitors) / len(competitors)

    if your_price > avg_price * 1.15:
        diff = round(((your_price - avg_price) / avg_price) * 100, 1)
        alerts.append(("🔴", "HIGH", f"Your price is **{diff}% above market average** (₹{round(avg_price,2)}). You are likely losing customers to cheaper sellers."))
    elif your_price > cheapest["price"]:
        diff = round(((your_price - cheapest["price"]) / cheapest["price"]) * 100, 1)
        alerts.append(("🟡", "MEDIUM", f"Your price is **{diff}% higher** than the cheapest competitor ({cheapest['title']} at ₹{cheapest['price']})."))

    if your_rating < avg_comp_rating - 0.5:
        alerts.append(("🔴", "HIGH", f"Your rating **{your_rating}/5** is significantly below competitor average **{round(avg_comp_rating,1)}/5**. Customers may choose competitors over you."))
    elif your_rating < best_rated["rating"]:
        alerts.append(("🟡", "MEDIUM", f"Your rating **{your_rating}/5** is lower than the top competitor **{best_rated['title']}** ({best_rated['rating']}/5)."))

    if your_score < 40:
        alerts.append(("🔴", "HIGH", f"Your sentiment score is **{your_score}/100** — majority of your reviews are negative. Immediate action needed."))
    elif your_score < 60:
        alerts.append(("🟡", "MEDIUM", f"Your sentiment score is **{your_score}/100** — more than 40% of reviews are negative."))

    if your_reviews == 0:
        alerts.append(("🟡", "MEDIUM", "You have **0 reviews**. Encourage buyers to leave reviews to build trust."))

    return alerts

def generate_insights(your_price, your_rating, your_reviews, your_neg, competitor_pos, competitors, avg_price):
    tips = []
    if not competitors:
        return ["No competitors found to compare."]

    cheapest      = min(competitors, key=lambda x: x["price"])
    best_rated    = max(competitors, key=lambda x: x["rating"])
    most_reviewed = max(competitors, key=lambda x: x["reviews"])

    if your_price > cheapest["price"]:
        diff = round(((your_price - cheapest["price"]) / cheapest["price"]) * 100, 1)
        tips.append(f"💰 Your price is **{diff}% higher** than the cheapest competitor ({cheapest['title']} at ₹{cheapest['price']}). Consider reducing your price.")
    if your_price > avg_price:
        tips.append(f"📊 Your price **₹{your_price}** is above market average **₹{round(avg_price, 2)}**. A price reduction could attract more buyers.")
    if your_rating < best_rated["rating"]:
        tips.append(f"⭐ Your rating **({your_rating}/5)** is lower than top competitor **{best_rated['title']}** ({best_rated['rating']}/5). Focus on improving product quality.")
    if your_reviews < most_reviewed["reviews"]:
        tips.append(f"💬 You have only **{your_reviews} reviews** vs competitor **{most_reviewed['reviews']} reviews**. Encourage buyers to leave reviews to build trust.")

    for neg in your_neg[:3]:
        if "delivery" in neg or "slow" in neg:
            tips.append(f"🚚 Your customers complain about **slow delivery**: *\"{neg}\"*. Partner with a faster courier service.")
        elif "packaging" in neg or "damaged" in neg:
            tips.append(f"📦 Your customers complain about **packaging**: *\"{neg}\"*. Improve packaging to prevent damage during shipping.")
        elif "quality" in neg or "broke" in neg or "cheap" in neg:
            tips.append(f"🔧 Your customers complain about **product quality**: *\"{neg}\"*. Source better quality materials.")
        elif "price" in neg or "worth" in neg or "money" in neg:
            tips.append(f"💸 Your customers feel the **price is not worth it**: *\"{neg}\"*. Either reduce price or improve product value.")
        else:
            tips.append(f"⚠️ Customer complaint: *\"{neg}\"*. Address this issue to improve your rating.")

    for pos in competitor_pos[:3]:
        if "delivery" in pos or "fast" in pos or "shipping" in pos:
            tips.append(f"🏆 Competitors are praised for **fast delivery**: *\"{pos}\"*. Improve your delivery speed to compete.")
        elif "quality" in pos or "excellent" in pos or "amazing" in pos:
            tips.append(f"🏆 Competitors are praised for **product quality**: *\"{pos}\"*. Match their quality standards to win more customers.")
        elif "price" in pos or "value" in pos or "worth" in pos:
            tips.append(f"🏆 Competitors are praised for **value for money**: *\"{pos}\"*. Consider adjusting your pricing strategy.")

    if not tips:
        tips.append("🎉 You are performing well against all competitors! Keep maintaining your quality and pricing.")
    return tips

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="E-Com Intelligence", page_icon="🛒", layout="wide")
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0d0d1a; }
  [data-testid="stSidebar"] { background: #111122; }
  h1,h2,h3,h4,p,label,div { color: #fff !important; }
  .stButton>button { background: linear-gradient(135deg,#e94560,#c62a47); color:#fff; border:none; border-radius:10px; padding:10px 28px; font-weight:600; width:100%; }
  .stButton>button:hover { opacity:0.85; }
  .stTextInput>div>input, .stNumberInput>div>input { background:#1a1a2e !important; color:#fff !important; border:1px solid #333; border-radius:8px; }
  div[data-baseweb="select"] > div { background:#1a1a2e !important; color:#fff !important; border:1px solid #333 !important; }
  .product-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius:16px; padding:24px; text-align:center; margin-bottom:10px; }
  .product-card:hover { border-color: #e94560; }
  .product-card .icon  { font-size:2.5rem; margin-bottom:10px; }
  .product-card .name  { font-size:1.1rem; font-weight:700; color:#fff; margin-bottom:6px; }
  .product-card .pid   { font-size:0.75rem; color:#888; margin-bottom:12px; }
  .product-card .price { font-size:1.3rem; font-weight:700; color:#e94560; margin-bottom:4px; }
  .product-card .meta  { font-size:0.82rem; color:#aaa; }
  .id-box { background:rgba(233,69,96,0.1); border:1px solid #e94560; border-radius:10px; padding:16px; margin:8px 0; text-align:center; }
  .review-tag { display:inline-block; padding:4px 10px; border-radius:20px; font-size:0.82rem; margin:3px; }
</style>
""", unsafe_allow_html=True)

# ── Session Init ──────────────────────────────────────────────────────────────
for key, val in [("page", "login"), ("seller", None)]:
    if key not in st.session_state:
        st.session_state[key] = val


def sidebar():
    st.sidebar.markdown("### 🛒 E-Com Intelligence")
    if st.session_state.seller:
        st.sidebar.markdown(f"👤 **{st.session_state.seller['seller_name']}**")
        st.sidebar.markdown(f"`{st.session_state.seller['seller_id']}`")
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Sign Out"):
            st.session_state.clear()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "login":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🛒 E-Com Intelligence")
        st.markdown("##### AI-Powered Competitive Analysis Platform")
        st.markdown("---")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login →"):
            seller = login_seller(username, password)
            if seller:
                st.session_state.seller = seller
                st.session_state.page   = "my_products"
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("Don't have an account?")
        if st.button("Register as New Seller →"):
            st.session_state.page = "register"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# REGISTER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "register":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 🆕 Register as New Seller")
        st.markdown("---")
        reg_username = st.text_input("Choose a Username")
        reg_password = st.text_input("Choose a Password", type="password")
        reg_confirm  = st.text_input("Confirm Password", type="password")
        seller_name  = st.text_input("Your Store Name", placeholder="e.g. TechZone Store")
        if st.button("✅ Create Account →"):
            if not all([reg_username, reg_password, reg_confirm, seller_name]):
                st.warning("Please fill in all fields.")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match.")
            elif len(reg_password) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                seller_id, error = register_seller(reg_username, reg_password, seller_name)
                if error:
                    st.error(error)
                else:
                    st.session_state.new_seller_id = seller_id
                    st.session_state.page = "register_success"
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Login"):
            st.session_state.page = "login"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# REGISTER SUCCESS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "register_success":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.success("🎉 Account Created Successfully!")
        st.markdown("### Your Unique Seller ID — Save This!")
        st.markdown(f"""
        <div class='id-box'>
            <p style='color:#aaa;font-size:0.85rem'>Your Seller ID</p>
            <h2 style='color:#e94560;letter-spacing:3px'>{st.session_state.new_seller_id}</h2>
        </div>
        """, unsafe_allow_html=True)
        st.warning("⚠️ Save your Seller ID. You will need it to manage your products.")
        if st.button("→ Go to Login"):
            st.session_state.page = "login"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MY PRODUCTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "my_products":
    sidebar()
    seller   = st.session_state.seller
    products = get_seller_products(seller["seller_id"])

    st.markdown(f"## 🏪 {seller['seller_name']} — My Products")
    st.markdown(f"Seller ID: `{seller['seller_id']}` | Total Products: **{len(products)}**")
    st.markdown("---")

    if not products:
        st.info("You have no products yet. Add your first product below!")
    else:
        st.markdown("### 📦 Select a Product to Analyze")
        st.markdown("Click **Analyze** on any product card to see full competitive intelligence.")
        st.markdown("<br>", unsafe_allow_html=True)
        cols_per_row = 3
        for i in range(0, len(products), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(products):
                    p    = products[i + j]
                    icon = get_icon(p["product_name"])
                    with col:
                        st.markdown(f"""
                        <div class='product-card'>
                            <div class='icon'>{icon}</div>
                            <div class='name'>{p['product_name'].title()}</div>
                            <div class='pid'>ID: {p['product_id']}</div>
                            <div class='price'>₹{p['price']}</div>
                            <div class='meta'>⭐ {p['rating']}/5 &nbsp;|&nbsp; 🚚 {p['delivery']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("🔎 Analyze", key=f"analyze_{p['product_id']}"):
                                st.session_state.selected_product = p
                                st.session_state.page = "dashboard"
                                st.rerun()
                        with btn_col2:
                            if st.button("🗑️ Remove", key=f"remove_{p['product_id']}"):
                                remove_product(seller["seller_id"], p["product_id"])
                                st.session_state.seller = load_db()[seller["seller_id"]]
                                st.success(f"✅ '{p['product_name'].title()}' removed.")
                                st.rerun()

    st.markdown("---")
    st.markdown("### ➕ Add New Product")
    with st.expander("Click to add a new product"):
        col1, col2 = st.columns(2)
        with col1:
            new_product_name = st.text_input("Product Type", placeholder="e.g. laptop, phone, tablet")
            new_price        = st.number_input("Your Selling Price (₹)", min_value=1.0, value=29999.0, step=1.0)
            new_delivery     = st.text_input("Delivery Time", value="2-4 days")
        with col2:
            new_rating  = st.slider("Your Product Rating (1-5)", 1, 5, 3)
        st.caption("✨ Customer reviews will be auto-generated based on your rating.")
        if st.button("✅ Add Product"):
            if not new_product_name:
                st.warning("Please enter a product type.")
            else:
                product_id, error = add_product(
                    seller["seller_id"], new_product_name,
                    new_price, new_rating, 0, new_delivery
                )
                if error:
                    st.error(error)
                else:
                    st.success(f"✅ Product added with auto-generated reviews! Product ID: **{product_id}**")
                    st.session_state.seller = load_db()[seller["seller_id"]]
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "dashboard":
    sidebar()
    seller  = st.session_state.seller
    product = st.session_state.selected_product

    if st.sidebar.button("← My Products"):
        st.session_state.page = "my_products"
        st.rerun()

    your_price   = product["price"]
    your_rating  = product["rating"]
    your_reviews = product["reviews"]
    icon         = get_icon(product["product_name"])

    # ── Scrape YOUR product reviews automatically ─────────────────────────────
    with st.spinner(f"🔍 Scraping real reviews for '{product['product_name']}'..."):
        your_review_texts = scrape_product_reviews(product["product_name"], max_reviews=20)
    if not your_review_texts:
        # fallback to dataset reviews if scrape returns nothing
        your_review_texts = product.get("review_texts") or REVIEWS_BY_RATING.get(your_rating, REVIEWS_BY_RATING[3])

    # ── Get Competitors: registered sellers first, then SerpApi, then fallback ─
    competitors  = get_competing_sellers(product["product_name"], seller["seller_id"])
    source_label = "Registered Sellers"
    if not competitors:
        with st.spinner(f"🌐 Fetching live market data from Google Shopping..."):
            competitors  = scrape_serpapi(product["product_name"], max_products=5)
            source_label = "Google Shopping (Live)"
    if not competitors:
        with st.spinner(f"Fetching fallback market data..."):
            competitors  = scrape_products(product["product_name"], max_items=5)
            source_label = "Market Data (Fallback)"

    if not competitors:
        st.error("❌ No competitor data found. Please try a different product name (e.g. laptop, phone, tablet).")
        st.stop()

    avg_price = round(sum(c["price"] for c in competitors) / len(competitors), 2)

    st.markdown(f"## {icon} {product['product_name'].title()} — Competitive Analysis")
    st.markdown(f"Store: **{seller['seller_name']}** | Product ID: `{product['product_id']}` | Comparing against: **{source_label}**")
    st.markdown("---")

    # ── Sentiment Analysis (needed for alerts) ────────────────────────────────
    if not is_model_ready():
        st.error("⚠️ Model not found. Run: `python3 train_model.py` first.")
        st.stop()

    your_pos, your_neg, your_score = analyze_reviews(your_review_texts)
    all_comp_reviews               = get_all_competitor_reviews(competitors)
    comp_pos, comp_neg, comp_score = analyze_reviews(all_comp_reviews)

    # ── ALERTS ────────────────────────────────────────────────────────────────
    alerts = generate_alerts(your_price, your_rating, your_reviews, your_score, competitors, avg_price)
    if alerts:
        st.markdown("### 🚨 Alerts")
        for emoji, level, msg in alerts:
            if level == "HIGH":
                st.error(f"{emoji} **[{level}]** {msg}")
            else:
                st.warning(f"{emoji} **[{level}]** {msg}")
        st.markdown("---")

    # ── Top Metrics ───────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Your Price",      f"₹{your_price}")
    col2.metric("⭐ Your Rating",      f"{your_rating}/5")
    col3.metric("📊 Market Avg Price", f"₹{avg_price}")
    st.markdown("---")

    # ── Comparison Table ──────────────────────────────────────────────────────
    st.markdown("### 📋 Seller Comparison")
    rows = [{"Seller": f"⭐ {seller['seller_name']} (YOU)", "Price (₹)": your_price,
             "Rating": your_rating, "Delivery": product["delivery"],
             "Sentiment Score": f"{your_score}/100"}]
    for c in competitors:
        c_reviews = c.get("review_texts", [])
        _, _, c_score = analyze_reviews(c_reviews) if c_reviews else ([], [], 50)
        rows.append({"Seller": c["title"], "Price (₹)": c["price"],
                     "Rating": c["rating"],
                     "Delivery": c["delivery"], "Sentiment Score": f"{c_score}/100"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("---")

    # ── Price Chart ───────────────────────────────────────────────────────────
    st.markdown("### 💰 Price Comparison")
    price_df = pd.DataFrame({
        "Seller":    [seller["seller_name"]] + [c["title"][:25] for c in competitors],
        "Price (₹)": [your_price] + [c["price"] for c in competitors]
    }).set_index("Seller")
    st.bar_chart(price_df)
    st.markdown("---")

    # ── YOUR Sentiment ────────────────────────────────────────────────────────
    st.markdown("### 🧠 Your Product — Sentiment Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("😊 Positive", len(your_pos))
    col2.metric("😞 Negative", len(your_neg))
    col3.metric("📊 Score",    f"{your_score}/100")
    st.progress(your_score / 100)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**😊 What customers like about YOUR product:**")
        for r in your_pos:
            st.success(f"✅ {r}")
        if not your_pos:
            st.info("No positive reviews found.")
    with col2:
        st.markdown("**😞 What customers dislike about YOUR product:**")
        for r in your_neg:
            st.error(f"❌ {r}")
        if not your_neg:
            st.info("No negative reviews found.")
    st.markdown("---")

    # ── COMPETITOR Sentiment ──────────────────────────────────────────────────
    st.markdown("### 🏆 Competitors — Sentiment Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("😊 Positive", len(comp_pos))
    col2.metric("😞 Negative", len(comp_neg))
    col3.metric("📊 Score",    f"{comp_score}/100")
    st.progress(comp_score / 100)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**😊 What customers love about COMPETITORS:**")
        for r in comp_pos[:5]:
            st.success(f"✅ {r}")
        if not comp_pos:
            st.info("No positive competitor reviews found.")
    with col2:
        st.markdown("**😞 What customers dislike about COMPETITORS:**")
        for r in comp_neg[:5]:
            st.error(f"❌ {r}")
        if not comp_neg:
            st.info("No negative competitor reviews found.")
    st.markdown("---")

    # ── AI Recommendations ────────────────────────────────────────────────────
    st.markdown("### 🤖 AI Recommendations")
    st.markdown("*Based on your review sentiment vs competitor strengths:*")
    tips = generate_insights(your_price, your_rating, your_reviews, your_neg, comp_pos, competitors, avg_price)
    for tip in tips:
        st.warning(tip)

    st.markdown("---")

    # ── Voice Read Aloud ─────────────────────────────────────────────────
    st.markdown("### 🔊 Voice Summary")

    if "speaking" not in st.session_state:
        st.session_state["speaking"] = False

    lines = []
    lines.append(f"Hello {seller['seller_name']}. Here is your product analysis summary for {product['product_name']}.")
    if alerts:
        lines.append("Alerts.")
        for _, level, msg in alerts:
            clean = msg.replace("**", "").replace("*", "").replace("`", "")
            lines.append(f"{level} alert. {clean}")
    lines.append("Recommendations.")
    for tip in tips:
        clean = tip.replace("**", "").replace("*", "").replace("`", "")
        lines.append(clean)
    lines.append(f"Your sentiment score is {your_score} out of 100.")
    if your_score >= 70:
        lines.append("Overall your product is performing well. Keep it up!")
    elif your_score >= 40:
        lines.append("Your product has room for improvement. Focus on the recommendations above.")
    else:
        lines.append("Your product needs immediate attention. Please act on the high alerts.")
    full_text = " ".join(lines)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔊 Read Aloud"):
            speak(full_text)
            st.success("🔊 Speaking... Check your speakers!")
    with col2:
        if st.button("⏹️ Stop"):
            stop_speaking()
            st.info("⏹️ Stopped.")
