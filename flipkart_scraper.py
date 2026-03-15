import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--window-size=1366,768")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def human_delay(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))

def is_blocked(driver):
    page = driver.page_source.lower()
    blocked_signs = ["captcha", "verify you are human", "access denied", "robot", "unusual traffic"]
    return any(sign in page for sign in blocked_signs)

def scrape_flipkart(product_name, max_products=6):
    """
    Scrapes Flipkart for a product name.
    Returns list of competitor products with real review texts.
    """
    driver = get_driver()
    results = []

    try:
        search_query = product_name.replace(" ", "+")
        url = f"https://www.flipkart.com/search?q={search_query}"
        print(f"🔍 Searching Flipkart for: {product_name}")
        driver.get(url)
        human_delay(2, 4)

        if is_blocked(driver):
            print("❌ Flipkart blocked the request. Please change your network (use mobile hotspot).")
            return []

        # Find product cards
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-id]")))
        except:
            pass

        # Try multiple card selectors (Flipkart changes layout often)
        cards = driver.find_elements(By.CSS_SELECTOR, "div._1AtVbE")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div._13oc-S")
        if not cards:
            cards = driver.find_elements(By.CSS_SELECTOR, "div._2kHMtA")

        print(f"Found {len(cards)} product cards")
        product_links = []

        for card in cards[:max_products + 3]:
            try:
                link_tag = card.find_element(By.CSS_SELECTOR, "a")
                href = link_tag.get_attribute("href")
                if href and "/p/" in href:
                    if href not in product_links:
                        product_links.append(href)
                if len(product_links) >= max_products:
                    break
            except:
                continue

        print(f"Found {len(product_links)} product links")

        # Visit each product page and scrape details + reviews
        for i, link in enumerate(product_links[:max_products]):
            try:
                print(f"Scraping product {i+1}/{len(product_links[:max_products])}...")
                driver.get(link)
                human_delay(2, 4)

                if is_blocked(driver):
                    print("❌ Blocked! Please switch to mobile hotspot and try again.")
                    break

                # Product title
                title = ""
                for sel in ["span.B_NuCI", "h1.yhB1nd", "span._35KyD6"]:
                    try:
                        title = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                        if title:
                            break
                    except:
                        continue

                # Price
                price = 0.0
                for sel in ["div._30jeq3._16Jk6d", "div._30jeq3", "div._25b18c"]:
                    try:
                        price_text = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                        price = float(price_text.replace("₹", "").replace(",", "").strip())
                        break
                    except:
                        continue

                # Rating
                rating = 0.0
                for sel in ["div._3LWZlK", "span._2_R_DZ"]:
                    try:
                        rating = float(driver.find_element(By.CSS_SELECTOR, sel).text.strip())
                        break
                    except:
                        continue

                # Review count
                review_count = 0
                for sel in ["span._2_R_DZ", "span._13vcmD"]:
                    try:
                        text = driver.find_element(By.CSS_SELECTOR, sel).text
                        nums = ''.join(filter(str.isdigit, text.split("Ratings")[0].replace(",", "")))
                        if nums:
                            review_count = int(nums)
                            break
                    except:
                        continue

                # Real review texts
                review_texts = []
                for sel in ["div.t-ZTKy", "div._6K-7Co", "div.row._3a0MFl"]:
                    try:
                        review_divs = driver.find_elements(By.CSS_SELECTOR, sel)
                        for r in review_divs[:8]:
                            text = r.text.strip()
                            if text and len(text) > 10:
                                review_texts.append(text)
                        if review_texts:
                            break
                    except:
                        continue

                # Delivery info
                delivery = "2-5 days"
                try:
                    delivery = driver.find_element(By.CSS_SELECTOR, "div._3XINqE").text.strip()
                except:
                    pass

                if title and price > 0:
                    results.append({
                        "title":        title[:60],
                        "price":        price,
                        "rating":       rating,
                        "reviews":      review_count,
                        "review_texts": review_texts if review_texts else [f"Product rated {rating}/5 by customers"],
                        "delivery":     delivery,
                        "url":          link,
                    })
                    print(f"✅ Scraped: {title[:40]} | ₹{price} | ⭐{rating} | 💬{len(review_texts)} reviews")

                human_delay(1.5, 3)

            except Exception as e:
                print(f"⚠️ Error scraping product {i+1}: {e}")
                continue

    except Exception as e:
        print(f"❌ Scraper error: {e}")
    finally:
        driver.quit()

    return results
