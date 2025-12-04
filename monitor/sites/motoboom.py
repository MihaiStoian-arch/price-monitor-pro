from bs4 import BeautifulSoup
import requests
import re

def scrape_motoboom_prices(product_url):
    """
    Extrage prețul RON de pe pagina unui produs Motoboom.
    """
    try:
        print(f"Încerc să extrag prețurile de la: {product_url}")
        
        # Setează un User-Agent pentru a evita blocarea
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()  # Ridică excepție pentru coduri de status HTTP proaste (4xx sau 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Selector care vizează span-ul care conține prețul RON, de obicei
        # sub clasa 'price' sau 'product-price', dar adesea marcat specific.
        # Încercăm un selector bazat pe clasa standard de preț, dar ajustăm.
        
        # Testăm selectorul robust (bazat pe font-size: 2rem din inspecția anterioară)
        price_element = soup.select_one('p.price span[style*="font-size: 2rem"]')
        
        # Dacă nu găsim elementul specific, încercăm selectorul general de preț
        if not price_element:
            price_element = soup.select_one('p.price .woocommerce-Price-amount') 
        
        if price_element:
            price_text = price_element.get_text(strip=True)
            
            # --- Curățarea și Conversia Prețului ---
            
            # 1. Elimină unitatea ("RON") și spațiile
            price_text = price_text.replace('RON', '').strip()
            
            # 2. Elimină separatorul de mii (punctul)
            price_text = price_text.replace('.', '') 
            
            # 3. Înlocuiește virgula cu punct pentru zecimale, dacă există
            price_text = price_text.replace(',', '.') 
            
            # 4. Asigură-te că string-ul final conține doar cifre și un punct
            cleaned_price = re.sub(r'[^\d.]', '', price_text)
            
            price_ron = float(cleaned_price)
            print(f"Preț RON extras: {price_ron} RON")
            return price_ron
        else:
            print("Eroare: Elementul de preț nu a fost găsit pe pagina Motoboom.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Eroare de rețea/request la Motoboom: {e}")
        return None
    except ValueError as e:
        print(f"Eroare de conversie a prețului (ValueError) la Motoboom: {e}. String curățat: '{cleaned_price}'")
        return None
    except Exception as e:
        print(f"Eroare generală la scraping Motoboom: {e}")
        return None