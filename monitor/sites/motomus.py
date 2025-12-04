import requests
from bs4 import BeautifulSoup
import re # Adaugam regex pentru curatarea valorii

def get_motomus_price(url):
    """Extrage pretul de pe motomus.ro folosind elementul hidden 'productFinalPrice'."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status() # Arunca exceptie pentru coduri de stare HTTP proaste (4xx sau 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Eroare la descarcarea paginii: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # 1. Cautarea elementului <input type="hidden" id="productFinalPrice">
    price_input = soup.find('input', {'id': 'productFinalPrice'})

    if price_input and 'value' in price_input.attrs:
        # 2. Extragerea valorii din atributul 'value'
        price_str = price_input['value']
        
        try:
            # 3. Conversia la float
            # Curatam stringul (daca ar contine virgule pentru mii)
            clean_price_str = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
            final_price = float(clean_price_str)
            return final_price
        except ValueError:
            print(f"Eroare: Valoarea '{price_str}' nu poate fi convertita in numar.")
            return None
    else:
        print("Eroare: Nu s-a gasit elementul 'productFinalPrice' sau atributul 'value'.")
        return None

# Exemplu de utilizare (rulabil direct):
if __name__ == '__main__':
    url_exemplu = "https://www.motomus.ro/kawasaki-adventure-tourer/kawasaki-versys-650-7.html"
    pret_ron = get_motomus_price(url_exemplu)

    if pret_ron:
        print(f"Pret RON extras de la Motomus: {pret_ron:.2f} RON")
    else:
        print("Extragerea pretului a esuat.")