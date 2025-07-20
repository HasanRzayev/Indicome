import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp',
    'Connection': 'keep-alive'}

def clean_price(text):
    match = re.search(r'([\d\.,]+)', text)
    if match:
        number = match.group(1).replace(",", "")
        return f"{number} $"
    return "Qiymət yoxdur"

def clean_link(link):
    if "rover.ebay.com" in link:
        parsed = urllib.parse.urlparse(link)
        query = urllib.parse.parse_qs(parsed.query)
        if 'mpre' in query:
            return query['mpre'][0]  # Original link
    return link

def is_relevant_title(title, query):
    title_lower = title.lower()
    query_words = query.lower().split()
    return any(word in title_lower for word in query_words)

def fetch_ebay(query):
    query_encoded = query.replace(" ", "+")
    url = f"https://www.ebay.com/sch/i.html?_nkw={query_encoded}"
    print(f"[eBay] Sorğu göndərilir: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        print(f"[eBay] Status kodu: {resp.status_code}")
    except Exception as e:
        print(f"[eBay] Xəta baş verdi: {e}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("li.s-item")
    print(f"[eBay] Tapılan məhsulların sayı: {len(items)}")
    results = []
    for item in items:
        title_tag = item.select_one(".s-item__title")
        link_tag = item.select_one("a.s-item__link")
        price_tag = item.select_one(".s-item__price")
        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            if not is_relevant_title(title, query):
                continue
            link = clean_link(link_tag["href"])
            price = clean_price(price_tag.get_text(strip=True) if price_tag else "")
            print(f"[eBay] Məhsul tapıldı: {title} | Qiymət: {price} | Link: {link}")
            results.append({"site":"eBay", "title": title, "link": link, "price": price})
            if len(results) >= 3:
                break
    return results


def fetch_walmart(query):
    query_encoded = query.replace(" ", "+")
    url = f"https://www.walmart.com/search?q={query_encoded}"
    print(f"[Walmart] Sorğu göndərilir: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        print(f"[Walmart] Status kodu: {resp.status_code}")
    except Exception as e:
        print(f"[Walmart] Xəta baş verdi: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("div[role='group'][data-item-id]")  # yeni struktur
    print(f"[Walmart] Tapılan məhsulların sayı: {len(items)}")

    results = []
    for item in items[:5]:
        try:
            # Başlıq
            title_tag = item.select_one("a span.w_iUH7")
            title = title_tag.get_text(strip=True) if title_tag else "Başlıq yoxdur"

            if not is_relevant_title(title, query):
                continue

            # Link
            link_tag = item.select_one("a")
            link = "https://www.walmart.com" + link_tag['href'] if link_tag and link_tag.has_attr('href') else "#"

            # Qiymət (əgər varsa)
            price_dollar = item.select_one("span.f2")
            price_cent = item.select_one("span.f6")
            price = "Qiymət yoxdur"
            if price_dollar:
                price = price_dollar.get_text(strip=True)
                if price_cent:
                    price += "." + price_cent.get_text(strip=True)
                price = f"{price} $"

            print(f"[Walmart] Məhsul tapıldı: {title} | Qiymət: {price} | Link: {link}")
            results.append({
                "site": "Walmart",
                "title": title,
                "link": link,
                "price": price
            })
        except Exception as e:
            print(f"[Walmart] Element işlənərkən xəta: {e}")
            continue

    return results

def fetch_etsy(query):
    query_encoded = query.replace(" ", "+")
    url = f"https://www.etsy.com/search?q={query_encoded}"
    print(f"[Etsy] Sorğu göndərilir: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        print(f"[Etsy] Status kodu: {resp.status_code}")
    except Exception as e:
        print(f"[Etsy] Xəta baş verdi: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("li.wt-list-unstyled div.v2-listing-card")
    print(f"[Etsy] Tapılan məhsulların sayı: {len(items)}")

    results = []
    for item in items[:5]:
        try:
            # Başlıq
            title_tag = item.select_one("h3")
            title = title_tag.get_text(strip=True) if title_tag else "Başlıq yoxdur"

            if not is_relevant_title(title, query):
                continue

            # Link
            link_tag = item.select_one("a.listing-link")
            link = link_tag['href'] if link_tag and link_tag.has_attr('href') else "#"

            # Qiymət
            price_tag = item.select_one("span.currency-value")
            price = price_tag.get_text(strip=True) + " $" if price_tag else "Qiymət yoxdur"
            print(price)
            print(f"[Etsy] Məhsul tapıldı: {title} | Qiymət: {price} | Link: {link}")
            results.append({
                "site": "Etsy",
                "title": title,
                "link": link,
                "price": price
            })
        except Exception as e:
            print(f"[Etsy] Element işlənərkən xəta: {e}")
            continue

    return results

def fetch_amazon(query):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    options = Options()
    # options.add_argument("--headless")  # lazım olsa aç
    options.add_argument("--headless")  # Başsız rejim (istəsən şərhə al)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.amazon.com/")
        wait = WebDriverWait(driver, 10)

        # Axtarış qutusunu tap
        search_box = wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        time.sleep(3)  # Məhsulların yüklənməsi üçün

        products = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")
        results = []

        for product in products[:10]:
            try:
                title = product.find_element(By.TAG_NAME, "h2").text
                link = product.find_element(By.TAG_NAME, "a").get_attribute("href")
                try:
                    price_whole = product.find_element(By.CLASS_NAME, "a-price-whole").text
                    price_fraction = product.find_element(By.CLASS_NAME, "a-price-fraction").text
                    price = f"${price_whole}.{price_fraction}"
                except:
                    continue
                results.append({
                    "site": "Amazon",
                    "title": title,
                    "price": price,
                    "link": link
                })
            except Exception as e:
                print(f"[Amazon Selenium] Elementdə xəta: {e}")
                continue

        return results

    finally:
        driver.quit()
def fetch_trendyol(query):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from bs4 import BeautifulSoup
    import time

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.trendyol.com")
        wait = WebDriverWait(driver, 20)

        search_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='suggestion']"))
        )
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        product_divs = soup.select("div.p-card-wrppr")

        results = []

        for product in product_divs:
            title_tag = product.select_one(".prdct-desc-cntnr-name")
            price_tag = product.select_one(".discounted")
            link_tag = product.find("a", href=True)

            if not title_tag or not price_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            price = price_tag.text.strip()
            link = "https://www.trendyol.com" + link_tag["href"].strip()

            if query.lower() in title.lower():
                results.append({
                    "site": "Trendyol",
                    "title": title,
                    "price": price,
                    "link": link
                })

        return results

    finally:
        driver.quit()
def fetch_aliexpress(query):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")  # Arxa planda işləsin istəsən aç
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    try:
        url = f"https://aliexpress.ru/wholesale?SearchText={query}"
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "red-snippet_RedSnippet__container__e15tmk"))
        )

        time.sleep(2)

        items = driver.find_elements(By.CLASS_NAME, "red-snippet_RedSnippet__container__e15tmk")
        results = []

        for item in items[:10]:  # yalnız ilk 10 nəticə
            try:
                title = item.find_element(By.CLASS_NAME, "red-snippet_RedSnippet__title__e15tmk").text
                price = item.find_element(By.CLASS_NAME, "red-snippet_RedSnippet__priceNew__e15tmk").text
                link = item.find_element(By.CSS_SELECTOR, "a.red-snippet_RedSnippet__gallery__e15tmk").get_attribute("href")
                image = item.find_element(By.CSS_SELECTOR, "img.gallery_Gallery__image__15bdcj").get_attribute("src")

                results.append({
                    "site": "AliExpress",
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": image
                })
            except Exception as e:
                print("⚠️ Bir məhsulda xəta:", e)
                continue

        return results

    finally:
        driver.quit()
def fetch_target(query):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")  # istəsən gizli modda işləsin
    options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=options)

    try:
        search_url = f"https://www.target.com/s?searchTerm={query}"
        driver.get(search_url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test="product-title"]'))
        )

        time.sleep(2)

        product_containers = driver.find_elements(By.CSS_SELECTOR, '[data-test="product-title"]')
        results = []

        for title_el in product_containers[:10]:
            try:
                title = title_el.text.strip()
                link = title_el.get_attribute("href")

                parent = title_el.find_element(By.XPATH, "./ancestor::div[@data-test='product-details']/..")

                try:
                    price_el = parent.find_element(By.CSS_SELECTOR, '[data-test="current-price"] span')
                    price = price_el.text.strip()
                except:
                    price = "N/A"

                results.append({
                    "site": "Target",
                    "title": title,
                    "price": price,
                    "link": link
                })

            except Exception as e:
                print("⚠️ Məhsulda xəta:", e)
                continue

        return results

    finally:
        driver.quit()

def search_all_sites(query):
    results = []
    results.extend(fetch_ebay(query))
    results.extend(fetch_walmart(query))
    results.extend(fetch_etsy(query))
    results.extend(fetch_amazon(query))
    results.extend(fetch_trendyol(query))
    results.extend(fetch_aliexpress(query))
    results.extend(fetch_target(query))

    if not results:
        print("⚠️ Heç bir nəticə tapılmadı.")
        return

    print(f"\nTapılan məhsulların ümumi sayı: {len(results)}\n")
    for product in results:
        print(f"🌐 Sayt: {product['site']}")
        print(f"🛍 Başlıq: {product['title']}")
        print(f"💰 Qiymət: {product['price']}")
        print(f"🔗 Link: {product['link']}")
        print("-" * 40)

if __name__ == "__main__":
    search_all_sites("iphone 15")
