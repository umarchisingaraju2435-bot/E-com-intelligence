import requests

SERPAPI_KEY = "4b1bfaaa2b5fb1b8e8e7ce53d3efa4967a75dde37a707ba19775f61da7573175"

def scrape_product_reviews(product_name, max_reviews=20):
    """
    Scrape real reviews for a product using Google Search snippets via SerpApi.
    Returns list of review text strings.
    """
    try:
        params = {
            "engine":  "google",
            "q":       f"{product_name} reviews site:amazon.in OR site:flipkart.com",
            "api_key": SERPAPI_KEY,
            "gl":      "in",
            "hl":      "en",
            "num":     10,
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = resp.json()

        reviews = []
        # extract snippets from organic results as review texts
        for result in data.get("organic_results", [])[:max_reviews]:
            snippet = result.get("snippet", "").strip()
            if snippet and len(snippet) > 10:
                # split snippet into sentences for more granular reviews
                sentences = [s.strip() for s in snippet.replace("...", ".").split(".") if len(s.strip()) > 10]
                reviews.extend(sentences[:3])
            if len(reviews) >= max_reviews:
                break

        print(f"✅ Scraped {len(reviews)} real review snippets for '{product_name}'")
        return reviews[:max_reviews]

    except Exception as e:
        print(f"❌ Review scrape failed: {e}")
        return []


def scrape_serpapi(product_name, max_products=5):
    """
    Fetch real Google Shopping competitor results via SerpApi.
    Returns list of competitor products with real scraped review snippets.
    """
    try:
        params = {
            "engine":  "google_shopping",
            "q":       product_name,
            "api_key": SERPAPI_KEY,
            "gl":      "in",
            "hl":      "en",
            "num":     max_products + 2,
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data     = response.json()

        if "error" in data:
            print(f"❌ SerpApi error: {data['error']}")
            return []

        results          = []
        shopping_results = data.get("shopping_results", [])

        for item in shopping_results[:max_products]:
            try:
                title     = item.get("title", "")[:60]
                price_raw = item.get("price", "0")
                price     = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_raw.replace(",", ""))) or 0)
                rating    = float(item.get("rating", 0) or 0)
                reviews   = int(item.get("reviews", 0) or 0)
                source    = item.get("source", "Online Store")
                delivery  = item.get("delivery", "2-5 days") or "2-5 days"

                # scrape real reviews for this competitor via Google Search
                review_texts = scrape_product_reviews(title, max_reviews=10)

                if title and price > 0:
                    results.append({
                        "title":        f"{source} — {title}"[:60],
                        "price":        price,
                        "rating":       rating if rating > 0 else 3.0,
                        "reviews":      reviews,
                        "delivery":     delivery,
                        "review_texts": review_texts,
                    })
                    print(f"✅ {title[:40]} | ₹{price} | ⭐{rating} | 💬{len(review_texts)} reviews")

            except Exception as e:
                print(f"⚠️ Skipping item: {e}")
                continue

        print(f"\n✅ SerpApi returned {len(results)} competitors for '{product_name}'")
        return results

    except Exception as e:
        print(f"❌ SerpApi request failed: {e}")
        return []
