import cloudscraper
from bs4 import BeautifulSoup
import re

def scrape_atvrom(url: str):
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "mobile": False
            }
        )

        response = scraper.get(url)

        if response.status_code != 200:
            print(f"[ATVROM] Status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Selector corect pentru pret:
        node = soup.select_one("h6.text-nowrap")
        if not node:
            print("[ATVROM] Nu am găsit elementul h6.text-nowrap")
            return None

        text = node.get_text(" ", strip=True)

        # extragere număr ex: "15.448 RON"
        match = re.search(r"([\d\.\, ]+)\s*RON", text)
        if not match:
            print("[ATVROM] Regex nu a găsit preț în text:", text)
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
