from requests_html import HTMLSession # NOU: Necesită requests-html și lxml_html_clean
from typing import Optional, Union
import re 

# Definește selectorul stabil (primul test)
# Pe baza analizei, ".product-price" eșuează. Încercăm un selector mai specific, sau generic.
PRICE_SELECTOR = "span.price" 

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
    print(f"    - Scrapează dealer.moto24.ro...")
    print(f"    - Încerc să extrag prețul de la: {product_url}")
    
    session = HTMLSession() 
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    try:
        response = session.get(product_url, headers=headers, timeout=20)
        
        # PAS CRITIC: Rulare JavaScript pentru a rezolva Cloudflare
        print("    - Încearcă rendering JavaScript (poate dura 5-10 secunde)...")
        response.html.render(sleep=2, timeout=10) 

        price_text = ""
        
        # 1. Încercăm selectorul specific
        price_element = response.html.find(PRICE_SELECTOR, first=True)

        if price_element:
            price_text = price_element.text
        else:
            # 2. Fallback: Căutăm în tot corpul paginii (mai lent, dar robust)
            body_element = response.html.find('body', first=True)
            if body_element:
                price_text = body_element.text

        final_price = None
        if price_text:
            # Căutăm în textul extras un format de preț care include puncte de separare de mii
            # Expresia regulată caută un număr formatat care se termină cu "Lei"
            price_match = re.search(r'([0-9\.]+)\s*Lei', price_text, re.IGNORECASE)
            
            if price_match:
                price_value = price_match.group(1) 
                final_price = clean_and_convert_price(price_value)
                
                if final_price:
                    print(f"      ✅ Succes. Preț extras din text: {final_price} RON")
                    return final_price
        
        print(f"      ❌ EROARE: Elementul de preț nu a fost găsit sau procesat corect.")
        return None
            
    except Exception as e:
        print(f"      ❌ EROARE la request/rendering către {product_url}: {e}")
        return None
    finally:
        session.close() 

if __name__ == '__main__':
    # Exemplu de URL de test
    test_url = "https://dealer.moto24.ro/aprilia-sr-gt-125-abs-2024/"
    pret_extras = scrape_moto24(test_url)
    
    if pret_extras is not None:
        print(f"\nRezultat final: {pret_extras} RON")
    else:
        print("\nExtragerea prețului a eșuat.")
