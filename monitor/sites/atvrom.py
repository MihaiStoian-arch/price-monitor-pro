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
        # try to clean strings like "12.768" or "12 768"
        try:
            s = str(v).replace(" ", "").replace(",", ".")
            return Decimal(s)
        except Exception:
            return None

def scrape_atvrom(url: str, timeout: int = 12) -> Optional[Decimal]:
    """
    Read the page, parse JSON-LD and return price in RON as Decimal.
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

    # find all JSON-LD scripts
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    if not scripts:
        print("[ATVROM] No ld+json scripts found")
    for s in scripts:
        raw = s.string
        if not raw:
            # sometimes script content embedded as children
            raw = "".join(map(str, s.contents)).strip()
        if not raw:
            continue
        # try to load JSON; many pages contain multiple JSON objects separated by newline -> try safe loads
        try:
            data = json.loads(raw)
        except Exception:
            # sometimes the script contains multiple JSON objects concatenated; try to extract the first {...}
            try:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                data = json.loads(raw[start:end])
            except Exception:
                # skip if cannot parse
                continue

        # Navigate schema.org structure: Product -> offers -> AggregateOffer or Offer
        if isinstance(data, dict) and data.get("@type") in ("Product", "product", "Product"):
            offers = data.get("offers")
            if not offers:
                continue

            # AggregateOffer with lowPrice/highPrice
            if isinstance(offers, dict):
                # try lowPrice / highPrice first
                low = offers.get("lowPrice") or offers.get("price") or offers.get("lowprice")
                if low is not None:
                    dec = _to_decimal(low)
                    if dec is not None:
                        return dec

                # offers may contain 'offers' list
                inner_offers = offers.get("offers")
                if inner_offers:
                    # inner_offers could be list or dict
                    if isinstance(inner_offers, dict):
                        p = inner_offers.get("price")
                        dec = _to_decimal(p)
                        if dec is not None:
                            return dec
                    elif isinstance(inner_offers, list):
                        # pick min or first available price. We'll choose low (min) to be safe.
                        prices = []
                        for o in inner_offers:
                            if isinstance(o, dict) and o.get("price") is not None:
                                dec = _to_decimal(o.get("price"))
                                if dec is not None:
                                    prices.append(dec)
                        if prices:
                            # return max/prioritize high if you want; here I return max (matches earlier code)
                            return max(prices)

            # If offers itself is a list of Offer items
            if isinstance(offers, list):
                prices = []
                for o in offers:
                    if isinstance(o, dict) and o.get("price") is not None:
                        dec = _to_decimal(o.get("price"))
                        if dec is not None:
                            prices.append(dec)
                if prices:
                    return max(prices)
    # if nothing found
    print("[ATVROM] No price found in JSON-LD")
    return None
