from bs4 import BeautifulSoup
import requests
import re
import time

def scrape_moto24(product_url):
    """
    Extrage prețul RON de pe pagina dealer.moto24.ro folosind un User-Agent robust 
    și selectori mai largi.
    """
    try:
        print(f"Încerc să extrag prețul de la: {product_url}")
        
        # User-Agent-ul folosit anterior, care ar trebui să evite blocarea 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Cerere HTTP
        response = requests.get(product_url, headers=headers, timeout=15)
        response.raise_for_status() # Ridică excepție pentru 4xx/5xx (inclusiv 403 Forbidden)

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Selectorul de Preț ---
        
        # 1. Încercăm selectorul bazat pe clasa principală de preț (din inspecția anterioară)
        # Acest selector ar trebui să prindă textul "23.824 Lei" sau similar.
        price_element = soup.select_one('p.product-price span[data-nosnippet]')
        
        # 2. Dacă nu găsim, încercăm selectorul general de preț (format cu Price-amount)
        if not price_element:
            price_element = soup.select_one('.woocommerce-Price-amount') 
            
        # 3. Dacă tot nu găsim, căutăm orice element cu o clasă care conține "price" sau "amount"
        if not price_element:
            price_element = soup.select_one('[class*="price"], [class*="amount"]')


        if price_element:
            # Luăm tot textul din element și din sub-elemente
            price_text = price_element.get_text(strip=True)
            
            # --- Curățarea și Conversia Prețului ---
            price_text = price_text.replace('.', '') # Elimină separatorul de mii (ex: 84.999 -> 84999)
            price_text = price_text.replace(',', '.') # Înlocuiește virgula cu punct pentru zecimale
            cleaned_price = re.sub(r'[^\d.]', '', price_text) # Păstrează doar cifre și punct
            
            if cleaned_price:
                price_ron = float(cleaned_price)
                print(f"Preț RON extras (Selector robust): {price_ron} RON")
                return price_ron
            
        # --- Soluția de rezervă (Regex pe tot conținutul) ---
        # Caută un număr care arată ca un preț mare, urmat de "Lei", "RON", "Eur" etc.
        price_match = re.search(r'(\d{1,3}(?:[,\.\s]\d{3})*(?:[,\.]\d{1,2})?)\s*(?:RON|Lei|EUR)', response.text, re.IGNORECASE)
        
        if price_match:
            price_text_regex = price_match.group(1)
            
            # Curățare: elimină spațiile și punctele (separatori de mii)
            price_text_regex = re.sub(r'[\s\.]', '', price_text_regex)
            # Înlocuiește virgula (separator zecimal) cu punct
            price_text_regex = price_text_regex.replace(',', '.')
            
            price_ron_regex = float(re.sub(r'[^\d.]', '', price_text_regex))
            print(f"Preț RON extras (Regex pe conținut): {price_ron_regex} RON")
            return price_ron_regex
        
        
        print("EROARE: Extragerea prețului a eșuat (Selector și Regex) pentru dealer.moto24.ro.")
        return None

    except requests.exceptions.HTTPError as e:
        # Aici prindem eroarea 403 Forbidden
        print(f"❌ EROARE HTTP: {e}. Extragerea prețului a eșuat (returnat None) pentru dealer.moto24.ro.")
        print(f"⚠️ Eroarea 403 persistă. IP-ul Runner-ului este **52.165.251.173**. Vă rugăm să cereți whitelisting-ul acestui IP.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Eroare de rețea/request: {e}. Extragerea prețului a eșuat (returnat None) pentru dealer.moto24.ro.")
        return None
    except Exception as e:
        print(f"❌ Eroare generală la scraping Moto24: {e}")
        return None
