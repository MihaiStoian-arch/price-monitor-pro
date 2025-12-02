# monitor/utils/requester.py

import requests
import logging

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8",
}

session = requests.Session()


def fetch_page(url: str):
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
        logging.warning(f"[ATVROM] Status code {r.status_code} for {url}")
        return None
    except Exception as e:
        logging.error(f"Request error for {url}: {e}")
        return None

