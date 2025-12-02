# monitor/sites/atvrom.py
import requests
from bs4 import BeautifulSoup
import json
from decimal import Decimal
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def _to_decimal(v) -> Optional[Decimal]:
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except Exception:
        try:
            s = str(v).replace(" ", "").replace(",", ".")
            return Decimal(s)
        except Exception:
            return None

def scrape_atvrom(url: str, timeout: int = 12) -> Optional[Decimal]:
    """
    Read the page, parse JSON-LD and return price in RON with 21% VAT included.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        print("[ATVROM] Request failed:", e)
        return None

    if r.status_code != 200:
        print(f"[ATVROM] Status code {r.status_code} for {url}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    if not scripts:
        print("[ATVROM] No ld+json scripts found")

    for s in scripts:
        raw = s.string or "".join(map(str, s.contents)).strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            try:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                data = json.loads(raw[start:end])
            except Exception:
                continue

        if isinstance(data, dict) and data.get("@type") == "Product":
            offers = data.get("offers")
            if not offers:
                continue

            if isinstance(offers, dict):
                low = offers.get("lowPrice") or offers.get("price")
                if low is not None:
                    dec = _to_decimal(low)
                    if dec is not None:
                        return (dec * Decimal("1.21")).quantize(Decimal("0.01"))

                inner_offers = offers.get("offers")
                if inner_offers:
                    prices = []
                    for o in inner_offers if isinstance(inner_offers, list) else [inner_offers]:
                        if isinstance(o, dict) and o.get("price"):
                            dec = _to_decimal(o["price"])
                            if dec:
                                prices.append(dec)
                    if prices:
                        final = max(prices)
                        return (final * Decimal("1.21")).quantize(Decimal("0.01"))

            if isinstance(offers, list):
                prices = []
                for o in offers:
                    if isinstance(o, dict) and o.get("price"):
                        dec = _to_decimal(o["price"])
                        if dec:
                            prices.append(dec)
                if prices:
                    final = max(prices)
                    return (final * Decimal("1.21")).quantize(Decimal("0.01"))

    print("[ATVROM] No price found in JSON-LD")
    return None
