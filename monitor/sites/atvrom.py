import cloudscraper
from bs4 import BeautifulSoup
import re

def scrape_atvrom(url: str):
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True
            }
        )

        # headers reale de browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache"
        }

        response = scraper.get(url, headers=headers)

        if response.status_code != 200:
            print(f"[ATVROM] Status: {response.status_code}")
            return None

        # DEBUG: salvăm HTML într-un fișier
        with open("atvrom_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        soup = BeautifulSoup(response.text, "html.parser")

        # selector alternativ pentru pret (am testat în browser)
        selectors = [
            "h6.text-nowrap",
            "div.product-price h6",
            "span.price-new",
            "span[itemprop='price']",
            ".product-price",
        ]

        price_node = None
        for sel in selectors:
            price_node = soup.select_one(sel)
            if price_node:
                break

        if not price_node:
            print("[ATVROM] Nu am găsit niciun selector de preț.")
            return None

        text = price_node.get_text(" ", strip=True)

        match = re.search(r"([\d\.\, ]+)\s*RON", text)
        if not match:
            print("[ATVROM] Regex ratat. Text =", text)
            return None

        cleaned = (
            match.group(1)
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
        )

        return float(cleaned)

    except Exception as e:
        print("[ATVROM] Eroare:", e)
        return None
