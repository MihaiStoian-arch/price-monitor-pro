from bs4 import BeautifulSoup
import re
import asyncio
from pyppeteer import launch
import time

# Selectorul specific pe care l-am identificat ca fiind cel mai fiabil
PRICE_SELECTOR = 'p.product-price span[data-nosnippet]'

def scrape_moto24(product_url):
    """
    Extrage prețul RON de pe pagina dealer.moto24.ro folosind Pyppeteer 
    pentru a randa conținutul generat de JavaScript.
    """
    # Pyppeteer rulează asincron. O funcție de wrapper este necesară.
    try:
        return asyncio.get_event_loop().run_until_complete(_scrape_moto24_async(product_url))
    except Exception as e:
        print(f"❌ EROARE GENERALĂ la Moto24 (Wrapper/Async): {e}")
        return None

async def _scrape_moto24_async(product_url):
    print(f"Încerc rendering JavaScript (Pyppeteer) pentru: {product_url}")
    browser = None
    try:
        # Lansăm browser-ul în mod headless (fără interfață grafică)
        browser = await launch(
            headless=True,
            # Argumente necesare pentru rularea în mediul GitHub Actions (runner-ul)
            args=['--no-sandbox', '--disable-setuid-sandbox'] 
        )
        page = await browser.newPage()
        
        # Setează un User-Agent (chiar dacă Pyppeteer trimite unul implicit, e bine să fie explicit)
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Navighează către URL și așteaptă ca rețeaua să se stabilizeze (sau maxim 30s)
        await page.goto(product_url, {'timeout': 30000, 'waitUntil': 'networkidle2'})
        
        # Așteaptă 3 secunde suplimentare pentru a permite JavaScript-ului să încarce prețul
        await asyncio.sleep(3) 

        # Extrage HTML-ul după randare
        content = await page.content()
        
        # --- Extragere Preț ---
        soup = BeautifulSoup(content, 'html.parser')
        
        # Selectorul precis identificat în inspecția HTML
        price_element = soup.select_one(PRICE_SELECTOR) 
        
        if price_element:
            price_text = price_element.get_text(strip=True)
            
            # --- Curățarea și Conversia Prețului ---
            price_text = price_text.replace('.', '') # Elimină separatorul de mii
            price_text = price_text.replace(',', '.') # Înlocuiește virgula cu punct pentru zecimale
            # Păstrează doar cifre și punct, eliminând "Lei", "RON", simboluri, etc.
            cleaned_price = re.sub(r'[^\d.]', '', price_text) 
            
            if cleaned_price:
                price_ron = float(cleaned_price)
                print(f"✅ Preț RON extras (Pyppeteer/JS): {price_ron} RON")
                return price_ron
            
        print(f"❌ EROARE: Elementul de preț cu selectorul '{PRICE_SELECTOR}' nu a fost găsit după randare.")
        return None

    except Exception as e:
        print(f"❌ EXCEPȚIE la Pyppeteer/Randare Moto24: {e}")
        return None
    finally:
        if browser:
            # Închide browser-ul (pas important pentru a elibera resursele)
            await browser.close()
