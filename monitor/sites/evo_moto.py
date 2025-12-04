import requests
from bs4 import BeautifulSoup
import re

# Selectori comuni pentru preț
COMMON_SELECTORS = [
    ".product-price",
    ".price",
    ".product-price-value",
    ".price-final",
    ".price-new",
    ".price-amount",
    ".woocommerce-Price-amount",
    ".amount",
    "[itemprop='price']",
    "#price",
    ".pret",
    ".pret_produs",
    ".product-main-price",
]

def clean_price(text):
    """Curăță și transformă un preț în Lei în integer.
    Am îmbunătățit funcția pentru a gestiona numerele cu format românesc (separare cu punct, zecimală cu virgulă).
    """
    if not text:
        return None

    # Curățăm textul: eliminăm RON/Lei și spațiile
    text = text.replace(" ", "").replace("lei", "").replace("Lei", "")
    
    # Expresia RegEx caută numere (inclusiv separatorul de mii '.' și zecimală ',')
    numbers_match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+)', text)

    if not numbers_match:
        return None

    price_string = numbers_match.group(1)
    
    # 1. Elimină separatorul de mii (punctul)
    # 2. Transformă virgula zecimală în punct
    price_string = price_string.replace('.', '').replace(',', '.')
    
    try:
        value = float(price_string)
        return int(value)
    except ValueError:
        return None


def scrape_evomoto(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    }

    with requests.Session() as session:
        session.headers.update(headers)
        
        # 2. **Simulăm schimbarea monedei în RON**
        base_url_match = re.match(r'(https?://[^/]+)', url)
        if base_url_match:
            base_url = base_url_match.group(1)
            
            # ATENȚIE: Am înlocuit URL-ul vechi cu un format mai comun:
            # Formatul original (Eroare 404): currency_change_url = f"{base_url}/currency/set/RON" 
            currency_change_url = f"{base_url}/?currency=ron" 
        else:
            print("Eroare: Nu s-a putut determina URL-ul de bază.")
            return None
        
        print(f"Încercare de schimbare a monedei în RON la: {currency_change_url}")

        try:
            # Folosim GET pentru a schimba moneda. Răspunsul așteptat este 200 sau 302.
            response_set_currency = session.get(currency_change_url, timeout=10, allow_redirects=True)
            print(f"Status schimbare monedă: {response_set_currency.status_code}")
            
            if response_set_currency.status_code not in (200, 302):
                print(f"Avertisment: Schimbarea monedei a eșuat sau a returnat status neașteptat ({response_set_currency.status_code}). Pagina ar putea fi în EUR.")

        except requests.exceptions.RequestException as e:
            print(f"Eroare la schimbarea monedei: {e}")
            # Nu returnăm None, ci încercăm oricum să extragem pagina

        # 3. Solicităm din nou pagina produsului (acum ar trebui să fie afișată în RON)
        print(f"Solicitarea paginii produsului: {url}")
        try:
            response = session.get(url, timeout=15)
        except requests.exceptions.RequestException as e:
            print(f"Eroare la solicitarea paginii: {e}")
            return None

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        all_prices_lei = []
        
        # 4. Extragem prețul din HTML
        for selector in COMMON_SELECTORS:
            element = soup.select_one(selector)
            
            if element:
                text = element.get_text(strip=True)
                
                # Verificăm dacă textul conține "lei" (indicând RON)
                if "lei" in text.lower():
                    value = clean_price(text)
                    if value:
                        print(f"Preț în RON găsit cu selectorul {selector}: {value} RON")
                        return value # Returnăm primul preț valid găsit

        # 5. Fallback: Căutăm orice număr mare (care ar putea fi prețul EUR sau RON)
        # Dacă scriptul ajunge aici, înseamnă că moneda NU s-a schimbat, sau selectorii sunt prea vagi.
        print("Avertisment: Nu a fost găsit preț care să conțină explicit 'lei'. Încercăm fallback-ul REGEX.")

        if not all_prices_lei:
            full_text = soup.get_text(" ", strip=True)
            # RegEx modificat pentru a căuta formatul românesc de numere
            matches = re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{1,2})\s*(?:Lei|lei|RON|ron)", full_text)

            for m in matches:
                clean = m.replace(".", "").replace(",", "") 
                # Presupunem că dacă nu are parte zecimală, este un preț întreg mare.
                if clean.isdigit():
                    all_prices_lei.append(int(clean))

        # 6. Returnăm cel mai mare preț (cel mai probabil prețul final)
        if all_prices_lei:
            return max(all_prices_lei)

        return None