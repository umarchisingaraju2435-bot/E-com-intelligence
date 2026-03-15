import requests
from bs4 import BeautifulSoup

BASE = "https://webscraper.io/test-sites/e-commerce/static"

CATEGORIES = {
    "laptop":      f"{BASE}/computers/laptops",
    "tablet":      f"{BASE}/computers/tablets",
    "phone":       f"{BASE}/phones/touch",
    "mobile":      f"{BASE}/phones/touch",
    "computer":    f"{BASE}/computers/laptops",
    "electronics": f"{BASE}/computers/laptops",
}

# Realistic reviews per rating — used for both your product and competitors
REVIEWS_BY_RATING = {
    1: [
        "very poor quality, broke after one day",
        "waste of money, not recommended",
        "terrible product, completely useless",
        "bad quality, very disappointed",
        "poor packaging, arrived damaged",
        "slow delivery and bad quality",
        "not as described, very unhappy",
        "cheap material, broke immediately",
    ],
    2: [
        "below average quality, not worth it",
        "poor packaging, could be better",
        "slow delivery, disappointing product",
        "not great quality for the price",
        "average at best, many issues",
        "delivery was slow and product mediocre",
        "not satisfied, expected better quality",
        "poor build quality, not recommended",
    ],
    3: [
        "average product, nothing special",
        "ok for the price, decent quality",
        "works fine but could be better",
        "average quality, delivery was ok",
        "nothing special but does the job",
        "decent product for the price",
        "average experience, not bad not great",
        "ok product, delivery was average",
    ],
    4: [
        "good quality product, happy with purchase",
        "value for money, fast delivery",
        "recommended, works as expected",
        "good build quality, satisfied",
        "fast delivery, good packaging",
        "happy with the purchase, good quality",
        "works well, good value for money",
        "solid product, good quality",
    ],
    5: [
        "excellent product, highly recommended",
        "amazing quality, best purchase ever",
        "superb quality, fast delivery",
        "outstanding product, exceeded expectations",
        "perfect product, love it",
        "brilliant quality, great packaging",
        "top quality, very satisfied",
        "fantastic product, will buy again",
    ],
}

def get_category_url(product_name):
    keyword = product_name.lower().strip()
    for key, url in CATEGORIES.items():
        if key in keyword:
            return url
    return f"{BASE}/computers/laptops"

def generate_review_texts(rating, description, count=6):
    """Generate realistic reviews mixing rating-based reviews with description keywords."""
    base_reviews = REVIEWS_BY_RATING.get(rating, REVIEWS_BY_RATING[3])
    # Extract keywords from description to make reviews feel product-specific
    keywords = [w for w in description.lower().split() if len(w) > 4][:3]
    extra = []
    if keywords:
        if rating >= 4:
            extra = [f"great {kw}, very satisfied" for kw in keywords]
        else:
            extra = [f"poor {kw}, not happy" for kw in keywords]
    all_reviews = base_reviews + extra
    return all_reviews[:count]

def scrape_products(product_name, max_items=6):
    url = get_category_url(product_name)
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        products = []
        for card in soup.select("div.thumbnail")[:max_items]:
            title       = card.select_one("a.title")["title"].strip()
            price       = float(card.select_one("h4.price").text.strip().replace("$", "").replace(",", ""))
            stars       = len(card.select("span.glyphicon-star:not(.glyphicon-star-empty)"))
            rating      = stars if stars > 0 else 3
            review_tag  = card.select_one("div.ratings p.pull-right")
            review_count = int(review_tag.text.replace("reviews", "").strip()) if review_tag else 0
            desc_tag    = card.select_one("p.description")
            description = desc_tag.text.strip() if desc_tag else ""
            review_texts = generate_review_texts(rating, description)
            products.append({
                "title":        title,
                "price":        price,
                "rating":       rating,
                "reviews":      review_count,
                "description":  description,
                "review_texts": review_texts,
                "delivery":     "2-4 days",
            })
        return products
    except:
        return []
