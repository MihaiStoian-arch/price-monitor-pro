import requests
from bs4 import BeautifulSoup
import re
from decimal import Decimal
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}

def _to_decimal(val: str) -> Optional[Decimal]:
    try:
        clean = (
            val.replace("Lei", "")
               .replace("LEI", "")
               .replace("lei", "")
               .replace(" ", "")
               .replace(".", "")
               .replace(",", ".")
        )
        return Decimal(clean)
    except:
        return None

def scrape_evomoto(url: str, timeout: int = 12) -> Optional[Decimal]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        print("[EVOMOTO] Request failed:", e)
        return None

    if r.status_code != 200:
        print(f"[EVOMOTO] Status {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Căutăm orice element care conține "Lei"
    node = soup.find(lambda tag: tag.name in ("span","div","p") and "lei" in tag.get_text().lower())

    if not node:
        print("[EVOMOTO] Nu am găsit prețul în lei.")
        return None

    text = node.get_text(" ", strip=True)

    # Regex robust: extrage 12.345,67 înainte de "Lei"
    match = re.search(r"([\d\.\, ]+)\s*Lei", text, flags=re.IGNORECASE)
    if not match:
        print("[EVOMOTO] Regex nu a găsit preț în text:", text)
        return None

    value = _to_decimal(match.group(1))
    if value is None:
        print("[EVOMOTO] Nu pot converti la Decimal:", match.group(1))
        return None

    return value
