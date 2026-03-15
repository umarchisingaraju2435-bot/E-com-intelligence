"""
Run this ONCE to seed 3 demo sellers with products and auto-assigned reviews.
    python3 seed_sellers.py
"""
from database import register_seller, add_product

SELLERS = [
    {
        "username":    "techzone",
        "password":    "1234",
        "seller_name": "TechZone Store",
        "products": [
            {"name": "laptop",  "price": 45000, "rating": 2, "reviews": 120, "delivery": "2-3 days"},
            {"name": "phone",   "price": 18000, "rating": 4, "reviews": 85,  "delivery": "1-2 days"},
        ]
    },
    {
        "username":    "rajstore",
        "password":    "1234",
        "seller_name": "Raj Electronics",
        "products": [
            {"name": "laptop",  "price": 39999, "rating": 4, "reviews": 200, "delivery": "3-4 days"},
            {"name": "tablet",  "price": 22000, "rating": 3, "reviews": 60,  "delivery": "2-4 days"},
        ]
    },
    {
        "username":    "megashop",
        "password":    "1234",
        "seller_name": "MegaShop India",
        "products": [
            {"name": "laptop",  "price": 42500, "rating": 5, "reviews": 350, "delivery": "1-2 days"},
            {"name": "phone",   "price": 15999, "rating": 3, "reviews": 140, "delivery": "2-3 days"},
            {"name": "tablet",  "price": 19999, "rating": 4, "reviews": 90,  "delivery": "1-3 days"},
        ]
    },
]

print("🌱 Seeding sellers...\n")
for s in SELLERS:
    seller_id, error = register_seller(s["username"], s["password"], s["seller_name"])
    if error:
        print(f"⚠️  {s['seller_name']}: {error}")
        continue
    print(f"✅ Registered: {s['seller_name']} | ID: {seller_id} | Login: {s['username']} / {s['password']}")
    for p in s["products"]:
        pid, err = add_product(seller_id, p["name"], p["price"], p["rating"], p["reviews"], p["delivery"])
        if err:
            print(f"   ⚠️  Product {p['name']}: {err}")
        else:
            print(f"   📦 Added: {p['name']} | ₹{p['price']} | ⭐{p['rating']}/5 | 💬{p['reviews']} reviews | ID: {pid}")
    print()

print("✅ Done! Now run: streamlit run app.py")
print("\n── Login Credentials ──────────────────")
for s in SELLERS:
    print(f"  {s['seller_name']:<20} → {s['username']} / {s['password']}")
