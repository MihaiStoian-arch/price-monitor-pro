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
        # ... (Pasul 1: session.get și response.html.render() ca mai sus) ...
        
        # Nou: Extrage tot textul din corp sau din elementul principal de produs
        # Vom încerca mai întâi selectorul specific, apoi tot body-ul
        price_element = response.html.find(PRICE_SELECTOR, first=True)

        if price_element:
            price_text = price_element.text
        else:
            # Fallback: Găsim tot body-ul și căutăm prețul în text
            print("      ❌ Selectorul nu a funcționat. Folosesc textul din body.")
            body_element = response.html.find('body', first=True)
            if body_element:
                price_text = body_element.text
            else:
                price_text = ""
        
        if price_text:
            # Folosim expresia regulată pentru a găsi formatul de preț (ex: 78.911 Lei)
            # Acesta va fi curățat oricum de clean_and_convert_price
            price_match = re.search(r'([0-9\.]+)\s*Lei', price_text)
            
            if price_match:
                price_value = price_match.group(1) # Ex: "78.911"
                final_price = clean_and_convert_price(price_value)
                
                print(f"      ✅ Succes. Preț extras din text: {final_price} RON")
                return final_price
            else:
                print("      ❌ EROARE: Nu s-a putut găsi prețul în textul paginii (format RON).")
                return None
        else:
            print("      ❌ EROARE: Nu s-a putut extrage text relevant din pagină.")
            return None
            
    except Exception as e:
        # ... (restul logicii de tratare a excepțiilor) ...
            
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
