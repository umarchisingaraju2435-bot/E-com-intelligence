import json
import os
import uuid

DB_FILE = "sellers.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def register_seller(username, password, seller_name):
    db = load_db()
    for sid, data in db.items():
        if data["username"] == username:
            return None, "Username already exists. Please choose another."
    seller_id = "SEL" + str(uuid.uuid4())[:5].upper()
    db[seller_id] = {
        "username":    username,
        "password":    password,
        "seller_name": seller_name,
        "seller_id":   seller_id,
        "products":    []
    }
    save_db(db)
    return seller_id, None

def assign_reviews(rating, product_name, count):
    """Auto-assign exactly `count` reviews based on rating and product name."""
    import random
    base    = REVIEWS_BY_RATING.get(rating, REVIEWS_BY_RATING[3]).copy()
    keyword = product_name.lower().strip()
    if rating >= 4:
        extra = [
            f"great {keyword}, very satisfied",
            f"excellent {keyword}, highly recommended",
            f"best {keyword} i have bought",
        ]
    elif rating <= 2:
        extra = [
            f"poor {keyword}, not happy",
            f"bad {keyword}, waste of money",
            f"terrible {keyword}, do not buy",
        ]
    else:
        extra = [
            f"average {keyword}, nothing special",
            f"decent {keyword} for the price",
        ]
    pool = base + extra
    # if count > pool size, repeat pool to fill
    while len(pool) < count:
        pool += base
    random.shuffle(pool)
    return pool[:count] if count > 0 else pool[:5]

def add_product(seller_id, product_name, price, rating, reviews, delivery):
    db = load_db()
    if seller_id not in db:
        return None, "Seller not found."
    product_id   = "PRD" + str(uuid.uuid4())[:5].upper()
    review_texts = assign_reviews(rating, product_name, reviews)
    product = {
        "product_id":   product_id,
        "product_name": product_name.lower().strip(),
        "price":        price,
        "rating":       rating,
        "reviews":      reviews,
        "delivery":     delivery,
        "review_texts": review_texts
    }
    db[seller_id]["products"].append(product)
    save_db(db)
    return product_id, None

def login_seller(username, password):
    db = load_db()
    for sid, data in db.items():
        if data["username"] == username and data["password"] == password:
            return data
    return None

def get_seller_products(seller_id):
    db = load_db()
    seller = db.get(seller_id)
    if seller:
        return seller.get("products", [])
    return []

def get_product(seller_id, product_id):
    products = get_seller_products(seller_id)
    for p in products:
        if p["product_id"] == product_id:
            return p
    return None

def remove_product(seller_id, product_id):
    db = load_db()
    if seller_id not in db:
        return False
    products = db[seller_id]["products"]
    db[seller_id]["products"] = [p for p in products if p["product_id"] != product_id]
    save_db(db)
    return True

def get_competing_sellers(product_name, current_seller_id):
    """
    Find all other registered sellers who sell the same product type.
    Returns list of dicts with seller info + matching product.
    """
    db = load_db()
    keyword = product_name.lower().strip()
    competitors = []
    for sid, data in db.items():
        if sid == current_seller_id:
            continue
        for p in data.get("products", []):
            if keyword in p["product_name"] or p["product_name"] in keyword:
                competitors.append({
                    "title":        data["seller_name"],
                    "price":        p["price"],
                    "rating":       p["rating"],
                    "reviews":      p["reviews"],
                    "delivery":     p["delivery"],
                    "seller_id":    sid,
                    "product_id":   p["product_id"],
                    "review_texts": p.get("review_texts") or REVIEWS_BY_RATING.get(p["rating"], REVIEWS_BY_RATING[3])
                })
                break
    return competitors

REVIEWS_BY_RATING = {
    1: ["very poor quality, broke after one day", "waste of money, not recommended", "terrible product", "bad quality, very disappointed", "poor packaging, arrived damaged"],
    2: ["below average quality, not worth it", "poor packaging, could be better", "slow delivery, disappointing", "not great quality for the price", "average at best, many issues"],
    3: ["average product, nothing special", "ok for the price, decent quality", "works fine but could be better", "decent product for the price", "average experience"],
    4: ["good quality product, happy with purchase", "value for money, fast delivery", "recommended, works as expected", "good build quality, satisfied", "fast delivery, good packaging"],
    5: ["excellent product, highly recommended", "amazing quality, best purchase ever", "superb quality, fast delivery", "outstanding product", "perfect product, love it"],
}
