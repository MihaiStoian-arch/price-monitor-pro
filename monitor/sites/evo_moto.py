import cloudscraper
from bs4 import BeautifulSoup
from decimal import Decimal
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}

def scrape_evomoto(url: str):
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False
        }
    )

    try:
        r = scraper.get(url, headers=HEADERS)
    except Exception as e:
        print("[EVOMOTO] Request failed:", e)
        return None

    if r.status_code != 200:
        print(f"[EVOMOTO] Status {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Caută prețul în lei
    price_node = soup.find("span", class_="price-lei-text")
    if not price_node:
        print("[EVOMOTO] No price found")
        return None

    text = price_node.get_text(strip=True)

    # Extrage număr (ex: 31.500 Lei)
    match = re.search(r"([\d\.\, ]+)", text)
    if not match:
        print("[EVOMOTO] Regex fail:", text)
        return None

    cleaned = match.group(1).replace(".", "").replace(" ", "").replace(",", ".")
    try:
        return Decimal(cleaned)
    except:
        return None
