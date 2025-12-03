import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}

def scrape_evomoto(url: str, timeout: int = 12) -> Optional[Decimal]:
    # 1. Luăm pagina (poate fi Cloudflare, nu contează)
    r = requests.get(url, headers=HEADERS, timeout=timeout)

    if r.status_code != 200:
        print("[EVOMOTO] Status", r.status_code)
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # 2. Cautăm ID-ul produsului
    product_div = soup.find("div", {"id": "product-detail"})
    if not product_div:
        print("[EVOMOTO] Nu pot găsi containerul de produs.")
        return None

    product_id = product_div.get("data-product-id")
    if not product_id:
        print("[EVOMOTO] Nu pot găsi product_id.")
        return None

    # 3. API intern pentru preț
    api_url = f"https://evo-moto.ro/product/getprice/{product_id}"

    r2 = requests.get(api_url, headers=HEADERS, timeout=timeout)

    if r2.status_code != 200:
        print("[EVOMOTO] API price status", r2.status_code)
        return None

    try:
        data = r2.json()
        price = data.get("price")
        if price:
            return Decimal(str(price))
    except Exception as e:
        print("[EVOMOTO] JSON parse error:", e)

    return None
