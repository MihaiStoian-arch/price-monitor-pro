import requests
from bs4 import BeautifulSoup

def get_jetskiadrenalin_price(url):
    """
    Extrage prețul dintr-un URL de produs de pe jetskiadrenalin.ro.
    
    :param url: URL-ul produsului.
    :return: Prețul sub formă de float sau None dacă extragerea eșuează.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Ridică excepție pentru coduri de stare HTTP greșite

        soup = BeautifulSoup(response.text, 'html.parser')

        # Selector CSS specific: Caută tag-ul <bdi> din interiorul structurii de preț.
        price_tag = soup.select_one('p.price span.woocommerce-Price-amount.amount bdi')

        if price_tag:
            # Extrage textul, elimină caracterele HTML și curăță
            price_text = price_tag.get_text(strip=True)
            
            # 1. Elimină spațiul non-breaking (u'\xa0') și punctul separator de mii.
            clean_price = price_text.replace(u'\xa0', '')
            clean_price = clean_price.replace('.', '')
            
            # 2. Elimină explicit simbolul 'lei' (insensibil la majuscule)
            clean_price = clean_price.lower().replace('lei', '')
            
            # 3. Elimină orice spații albe rămase
            clean_price = clean_price.strip()

            # Convertește în float
            try:
                price = float(clean_price)
                return price
            except ValueError:
                # Această eroare ar trebui să fie rezolvată acum, dar o păstrăm pentru siguranță
                print(f"Eroare de conversie a prețului: '{clean_price}' nu este un număr valid.")
                return None
        
        else:
            print("Elementul de preț nu a fost găsit cu selectorul specificat.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"A apărut o eroare la solicitarea URL-ului: {e}")
        return None

if __name__ == '__main__':
    # Rularea funcției direct pentru testare rapidă
    test_url = "https://jetskiadrenalin.ro/can-am-outlander-max-xt-p-t-abs-1000r-2026/"
    price = get_jetskiadrenalin_price(test_url)
    if price:
        print(f"Prețul extras este: {price} LEI")
    else:
        print("Testul direct nu a reușit să extragă prețul.")