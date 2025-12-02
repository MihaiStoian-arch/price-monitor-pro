# monitor/price_extractor.py

import re
from decimal import Decimal


def extract_price_from_text(text: str):
    """
    Extrage și returnează cel mai mare preț în RON dintr-un text.
    Acceptă formate:
      12.345 lei
      12 345 lei
      12.345,99 lei
      12345 Lei
    """
    if not text:
        return None

    pattern = r"(\d[\d\.\s\,]*)\s*(lei|ron)"
    matches = re.findall(pattern, text.lower())

    prices = []
    for raw, _ in matches:
        cleaned = (
            raw.replace(" ", "")
               .replace(".", "")
               .replace(",", ".")
        )
        try:
            prices.append(Decimal(cleaned))
        except:
            pass

    if not prices:
        return None

    return max(prices)

