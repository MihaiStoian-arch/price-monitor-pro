from bs4 import BeautifulSoup
import requests
import re
import time

def scrape_moto24(product_url):
    """
    Extrage prețul RON de pe pagina unui produs dealer.moto24.ro folosind cerere directă.
    Abordarea este similară cu Motoboom, folosind un User-Agent robust.
    
    În cazul în care serverul blochează cererea (403), încercarea cu User-Agent ar trebui să rezolve.
    """
    
    # ----------------------------------------------------
    # ⚠️ Dacă eroarea 403 persistă, folosiți adresa IP externă afișată în log (52.165.251.173) 
    # și rugați administratorul site-ului dealer.moto24.ro să o adauge în whitelist.
    # ----------------------------------------------------

    try:
        print(f"Încerc să extrag prețul de la: {product_url}")
        
        # User-Agent-ul folosit anterior, care ar trebui să evite blocarea 403
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(product_url, headers=headers, timeout=15)
        response.raise_for_status()  # Ridică excepție pentru 4xx/5xx

        # Dacă pagina nu necesită JavaScript, BeautifulSoup va funcționa.
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Selectorul de Preț ---
        # Selectorul este preluat din inspecția elementului de preț de pe o pagină similară.
        # De obicei, este un div, span sau p cu o clasă specifică, cum ar fi 'product-price'.
        
        # 1. Încercăm selectorul cel mai probabil, bazat pe structura unui magazin online (WooCommerce sau similar):
        price_element = soup.select_one('.price .woocommerce-Price-amount')
        
        # 2. Dacă nu găsim, încercăm selectorul general de preț:
        if not price_element:
            price_element = soup.select_one('.product-price') 
            
        # 3. Dacă tot nu găsim, încercăm o clasă care conține valoarea numerică de preț
        if not price_element:
             price_element = soup.select_one('.price-big-container .price') 

        if price_element:
            price_text = price_element.get_text(strip=True)
            
            # --- Curățarea și Conversia Prețului ---
            
            # 1. Elimină separatorul de mii (punctul)
            price_text = price_text.replace('.', '')
            
            # 2. Înlocuiește virgula cu punct pentru zecimale (de exemplu, 84.999,00 -> 84999.00)
            price_text = price_text.replace(',', '.')
            
            # 3. Elimină orice caracter non-numeric sau non-punct (inclusiv RON, € sau alte simboluri)
            cleaned_price = re.sub(r'[^\d.]', '', price_text)
            
            # Asigurăm că nu returnăm un string gol
            if cleaned_price:
                price_ron = float(cleaned_price)
                print(f"Preț RON extras (HTML direct): {price_ron} RON")
                return price_ron
            
        # --- Soluția de rezervă (Regex) ---
        # Dacă selectorul eșuează (elementul e ascuns sau lipsește), căutăm prețul 
        # direct în tot conținutul HTML folosind regex.
        
        # Caută un număr care ar putea fi un preț mare (ex: de la 5 cifre în sus)
        # Regex pentru formatul: Cifre.Cifre.Cifre,Cifre sau Cifre Cifre Cifre,Cifre
        price_match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*RON', response.text.replace(' ', ''), re.IGNORECASE)
        
        if price_match:
            price_text_regex = price_match.group(1)
            
            # Curățare similară
            price_text_regex = price_text_regex.replace('.', '')
            price_text_regex = price_text_regex.replace(',', '.')
            
            price_ron_regex = float(re.sub(r'[^\d.]', '', price_text_regex))
            print(f"Preț RON extras (Regex): {price_ron_regex} RON")
            return price_ron_regex
        
        
        # Dacă ambele soluții eșuează
        print("EROARE: Extragerea prețului a eșuat (Element sau Regex) pentru dealer.moto24.ro.")
        return None

    except requests.exceptions.HTTPError as e:
        print(f"EROARE HTTP: {e}. Extragerea prețului a eșuat (returnat None) pentru dealer.moto24.ro.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Eroare de rețea/request: {e}. Extragerea prețului a eșuat (returnat None) pentru dealer.moto24.ro.")
        return None
    except ValueError as e:
        # Aici prindem eroarea dacă float() eșuează
        print(f"Eroare de conversie a prețului (ValueError) la Moto24: {e}. String curățat: '{cleaned_price}'")
        return None
    except Exception as e:
        print(f"Eroare generală la scraping Moto24: {e}")
        return None

# Exemplu de utilizare (pentru testare locală, nu trebuie inclus în fișierul final)
# if __name__ == '__main__':
#     test_url = "https://dealer.moto24.ro/atv-can-am-outlander-max-xt-700-t-abs-2025/"
#     price = scrape_moto24(test_url)
#     print(f"Preț final: {price}")
