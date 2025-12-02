# monitor/sites/atvrom.py

import re
from decimal import Decimal
from bs4 import BeautifulSoup

from monitor.utils.requester import fetch_page
from monitor.price_extractor import extract_price_from_text


def scrape_atvrom(url: str):
    """
    Returnează prețul final în RON de pe ATVROM.
    """
    html = fetch_page(url)
    if html is None:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # 1. Selectorul specific ATVROM (cel mai stabil)
    price_node = soup.select_one("h6.text-nowrap")
    if price_node:
        price = extract_price_from_text(price_node.get_text(" ", strip=True))
        if price:
            return price

    # 2. Fallback – caută în orice text
    return extract_price_from_text(soup.get_text(" ", strip=True))

