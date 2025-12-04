import requests # <--- ESEȚIAL: Am adăugat importul 'requests' aici!
from bs4 import BeautifulSoup 
import re 
from typing import Optional, Union

# Definește selectorul stabil pentru preț
PRICE_SELECTOR = ".product-price" 

def clean_and_convert_price(price_text: str) -> Optional[int]:
    """
    Curăță textul prețului (e.g., "23.824 Lei (TVA Inclus)") și îl convertește în RON întreg (int).
    """
    if not price_text:
        return None
        
    # 1. Elimină textul irelevant (Lei, TVA Inclus, etc.)
    # Ex: "23.824 Lei (TVA Inclus)" -> "23.824"
    cleaned_text = re.sub(r'[^0-9\.]', '', price_text) 
    
    # 2. Elimină separatorul de mii (punctul).
    # Ex: "23.824" -> "23824"
    final_numeric_string = cleaned_text.replace('.', '')
    
    try:
        # 3. Convertește în număr întreg (RON)
        price_ron = int(final_numeric_string)
        return price_ron
    except ValueError:
        print(f"Eroare la conversia prețului '{final_numeric_string}' în număr întreg.")
        return None

def scrape_moto24(product_url: str) -> Optional[int]:
    """
    Descarcă pagina, extrage prețul în RON și returnează valoarea numerică.
    """
    print(f"Încerc să extrag prețul de la: {product_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Aici folosește 'requests.get'
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status() # Ridică excepție pentru coduri HTTP de eroare (4xx sau 5xx)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Găsește elementul de preț folosind selectorul '.product-price'
        price_element = soup.select_one(PRICE_SELECTOR)
        
        if price_element:
            # Extrage tot textul din elementul părinte
            price_text = price_element.get_text(strip=True)
            
            # Curăță și convertește prețul
            final_price = clean_and_convert_price(price_text)
            
            print(f"Preț text original extras din site: '{price_text}'")
            print(f"Preț numeric curățat: {final_price} RON")
            return final_price
        else:
            print(f"Eroare: Elementul de preț cu selectorul '{PRICE_SELECTOR}' nu a fost găsit.")
            return None
        
    except requests.exceptions.RequestException as e: # Aici folosește 'requests.exceptions'
        print(f"Eroare de rețea/request: {e}")
        return None
    except Exception as e:
        print(f"A apărut o eroare neașteptată: {e}")
        return None

# Exemplu de utilizare pentru testare:
if __name__ == '__main__':
    # URL-ul tău din imagine
    test_url = "https://dealer.moto24.ro/aprilia-sr-gt-125-abs-2024/"
    
    pret_extras = scrape_moto24(test_url)
    
    if pret_extras is not None:
        print(f"\nRezultat final: {pret_extras} RON")
    else:
        print("\nExtragerea prețului a eșuat.")