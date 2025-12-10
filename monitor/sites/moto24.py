from requests_html import HTMLSession
from typing import Optional, Union
import re 

PRICE_SELECTOR = ".product-price" # Selectorul actualizat pentru moto24, bazat pe log-uri.

def clean_and_convert_price(price_text: str) -> Optional[float]:
    """Curăță textul prețului (e.g., "23.824 Lei") și îl convertește în float."""
    if not price_text:
        return None
    # Elimină orice non-cifră în afară de punct și virgulă
    cleaned_text = re.sub(r'[^\d\.,]', '', price_text) 
    
    # 1. Înlocuim punctul (separator de mii) cu nimic. 
    # 2. Înlocuim virgula (separator zecimal) cu punct. 
    # (Acest lucru este valabil pentru formatul românesc standard: "12.345,67" -> "12345.67")
    
    # Verificăm dacă există virgulă pentru a ști unde este zecimala
    if ',' in cleaned_text:
        # Separator de mii punct, separator zecimal virgulă
        final_numeric_string = cleaned_text.replace('.', '').replace(',', '.')
    else:
        # Presupunem că dacă nu există virgulă, tot textul este număr întreg (sau separatorul este punct)
        final_numeric_string = cleaned_text.replace('.', '')
        
    try:
        price_float = float(final_numeric_string)
        return price_float
    except ValueError:
        return None

def scrape_moto24(product_url: str) -> Optional[float]:
    """Descarcă pagina folosind rendering JavaScript pentru a trece de protecțiile anti-bot (403)."""
    
    session = HTMLSession() 
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    try:
        response = session.get(product_url, headers=headers, timeout=25)
        
        # PAS CRITIC: Rulare JavaScript (pentru 403)
        print("      - Încearcă rendering JavaScript (poate dura 5-10 secunde)...")
        # Folosim waitUntil='domcontentloaded' pentru a fi mai rapid decât 'networkidle'
        response.html.render(sleep=3, timeout=15, reload=False) 

        # 1. Încercăm selectorul specific (.product-price)
        price_element = response.html.find(PRICE_SELECTOR, first=True)

        price_text = None
        if price_element:
            price_text = price_element.text
            print(f"      - Text preț găsit via selector: '{price_text}'")
        else:
            print(f"      ❌ EROARE: Elementul de preț cu selectorul '{PRICE_SELECTOR}' nu a fost găsit după rendering.")
            
            # 2. Fallback: Căutăm în tot textul paginii (după ce a fost randată)
            body_text = response.html.full_text
            price_match = re.search(r'([0-9\.\,]+)\s*Lei', body_text, re.IGNORECASE)
            
            if price_match:
                price_text = price_match.group(1)
                print(f"      - Text preț găsit via regex: '{price_text}'")
            else:
                print(f"      ❌ EROARE: Niciun preț găsit folosind regex.")
                return None
        
        final_price = clean_and_convert_price(price_text)
        
        if final_price:
            return final_price
        else:
            print(f"      ❌ EROARE: Prețul '{price_text}' nu a putut fi convertit în număr.")
            return None
            
    except Exception as e:
        print(f"      ❌ EXCEPȚIE la request/rendering către dealer.moto24.ro: {e}")
        return None
    finally:
        session.close() 

if __name__ == '__main__':
    # Exemplu de URL de test (Outlander 700)
    test_url = "https://dealer.moto24.ro/atv-can-am-outlander-max-xt-700-t-abs-2025/"
    pret_extras = scrape_moto24(test_url)
    
    if pret_extras is not None:
        print(f"\nRezultat final: {pret_extras:.2f} RON")
    else:
        print("\nExtragerea prețului a eșuat.")
