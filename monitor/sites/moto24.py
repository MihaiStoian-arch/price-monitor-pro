from requests_html import HTMLSession # NOU: Am înlocuit 'requests' cu 'HTMLSession'
from typing import Optional, Union
import re 
import time

# Definește selectorul stabil pentru preț
PRICE_SELECTOR = ".product-price" 

def clean_and_convert_price(price_text: str) -> Optional[int]:
    """
    Curăță textul prețului (e.g., "23.824 Lei (TVA Inclus)") și îl convertește în RON întreg (int).
    """
    if not price_text:
        return None
        
    # 1. Elimină textul irelevant (Lei, TVA Inclus, etc.)
    cleaned_text = re.sub(r'[^0-9\.]', '', price_text) 
    
    # 2. Elimină separatorul de mii (punctul).
    final_numeric_string = cleaned_text.replace('.', '')
    
    try:
        # 3. Convertește în număr întreg (RON)
        price_ron = int(final_numeric_string)
        return price_ron
    except ValueError:
        return None

def scrape_moto24(product_url: str) -> Optional[int]:
    """
    Descarcă pagina folosind rendering JavaScript pentru a trece de protecțiile anti-bot.
    """
    print(f"Încerc să extrag prețul de la: {product_url}")
    
    session = HTMLSession() # Creăm o sesiune HTML
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    try:
        # Pasul 1: Obținerea paginii
        response = session.get(product_url, headers=headers, timeout=20)
        
        # ⚠️ PAS CRITIC: Rulare JavaScript pentru a rezolva Cloudflare (timeout 10 secunde)
        print("    - Încearcă rendering JavaScript (poate dura 5-10 secunde)...")
        # sleep=2 așteaptă 2 secunde după încărcarea inițială, asigurând că scripturile se execută.
        response.html.render(sleep=2, timeout=10) 

        # Pasul 2: Extragerea prețului după rendering (folosind sintaxa requests-html)
        price_element = response.html.find(PRICE_SELECTOR, first=True)

        if price_element:
            # Extrage textul (acum este cel final, generat de JS)
            price_text = price_element.text
            final_price = clean_and_convert_price(price_text)
            
            # print(f"      Preț text original extras după rendering: '{price_text}'")
            print(f"      ✅ Succes. Preț extras: {final_price} RON")
            return final_price
        else:
            print(f"      ❌ EROARE: Elementul de preț cu selectorul '{PRICE_SELECTOR}' nu a fost găsit după rendering.")
            return None
            
    except Exception as e:
        print(f"      ❌ EROARE la request/rendering către {product_url}: {e}")
        return None
    finally:
        # Foarte important: închide sesiunea după utilizare
        session.close() 

if __name__ == '__main__':
    # Exemplu de URL de test
    test_url = "https://dealer.moto24.ro/atv-can-am-outlander-1000r-xtp-t-abs-2025/"
    pret_extras = scrape_moto24(test_url)
    
    if pret_extras is not None:
        print(f"\nRezultat final: {pret_extras} RON")
    else:
        print("\nExtragerea prețului a eșuat.")
