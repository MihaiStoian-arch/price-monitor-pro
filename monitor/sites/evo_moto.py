import cloudscraper
from bs4 import BeautifulSoup
from decimal import Decimal
import json
from typing import Optional

def _to_decimal(v) -> Optional[Decimal]:
    if v is None:
        return None
    s = str(v).replace(" ", "").replace(",", "").replace(".", "")
    try:
        return Decimal(s)
    except:
        return None

def scrape_evomoto(url: str):
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "mobile": False
        }
    )

    try:
        r = scraper.get(url)
    except Exception as e:
        print("[EVOMOTO] Request failed:", e)
        return None

    if r.status_code != 200:
        print(f"[EVOMOTO] Status {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Caută JSON-LD ca la ATVROM
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    for s in scripts:
        raw = s.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except:
            continue

        if isinstance(data, dict) and data.get("@type") == "Product":
            offers = data.get("offers")
            if not offers:
                continue

            price = None
            if isinstance(offers, dict):
                price = offers.get("price")
            if price:
                return Decimal(price)

    print("[EVOMOTO] No price found")
    return None
