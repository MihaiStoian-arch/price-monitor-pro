# monitor/sites/moto4all.py

import requests
from bs4 import BeautifulSoup
import re # Asigură-te că ai importat 're'

def scrape_moto4all_prices(url):
    """
    Extrage pretul in RON de pe o pagina moto4all, folosind structura specifica.
    Returneaza pretul in RON (float).
    """
    print(f"Încerc să extrag prețul (RON) de la: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Găsim elementul div părinte 'new_price'
        price_container = soup.find('div', class_='new_price')
        
        if price_container:
            # 2. Găsim partea întreagă (m_int)
            integer_part_tag = price_container.find('span', class_='m_int')
            
            # 3. Găsim partea zecimală (m_dec)
            decimal_part_tag = price_container.find('span', class_='m_dec')
            
            if integer_part_tag and decimal_part_tag:
                
                # Curățăm partea întreagă: Păstrăm DOAR cifrele
                int_text = integer_part_tag.text.strip()
                # Eliminăm orice caracter care NU este cifră ('\d')
                int_str = re.sub(r'[^\d]', '', int_text) 
                
                # Curățăm partea zecimală: Păstrăm DOAR cifrele
                dec_text = decimal_part_tag.text.strip()
                dec_str = re.sub(r'[^\d]', '', dec_text)
                
                # Construim string-ul de preț complet: '99641.69'
                full_price_str = f"{int_str}.{dec_str}"
                
                print(f"Debugging: String-ul final de preț este: '{full_price_str}'")
                
                try:
                    price_ron = float(full_price_str)
                    return price_ron
                except ValueError as ve:
                    # Capturăm excepția pentru a vedea exact de ce nu se convertește
                    print(f"Eroare: Nu s-a putut converti în număr prețul '{full_price_str}'. Detalii: {ve}")
                    return None
            else:
                print("Eroare: Nu s-au găsit părțile (m_int/m_dec) ale prețului.")
                return None
        else:
            print("Eroare: Eticheta (tag-ul) cu prețul ('div', class_='new_price') nu a fost găsită.")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Eroare de rețea la accesarea URL-ului: {e}")
        return None