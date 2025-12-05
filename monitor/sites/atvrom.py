import requests
import xml.etree.ElementTree as ET

# URL-ul feed-ului XML specificat
FEED_URL = "https://www.atvrom.ro/storage/feed/vehicleFeed.xml"
TVA_RATE = 0.21

def get_atvrom_price_map(url=FEED_URL):
    """
    Descarcă feed-ul XML al ATVROM, extrage prețul fără TVA (price_ron),
    aplică TVA 21% și returnează o hartă {URL: Preț_Final_Cu_TVA}.
    """
    print(f"📥 [ATVROM] Descarc feed-ul XML de la: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status() 
        
        root = ET.fromstring(response.content)
        price_map = {}
        
        # Iterăm prin elementele 'product'
        for product in root.findall('product'): 
            link_element = product.find('link')
            price_element = product.find('price_ron') # Prețul FĂRĂ TVA
            
            if link_element is not None and price_element is not None:
                product_link = link_element.text.strip()
                
                # Curățăm și convertim prețul de bază în float
                try:
                    # Eliminăm ' RON' și spațiile
                    base_price_str = price_element.text.replace(' RON', '').strip()
                    price_without_vat = float(base_price_str)
                    
                    # Aplicăm formula: Preț Final = Preț Fără TVA * (1 + 0.21)
                    final_price_with_vat = price_without_vat * (1 + TVA_RATE)
                    
                    # Rotunjim la cel mai apropiat întreg sau două zecimale, 
                    # în funcție de precizia dorită. Aleg rotunjirea la întreg
                    # pentru a se potrivi cu formatul RON obișnuit.
                    price_map[product_link] = str(round(final_price_with_vat))
                    
                except ValueError as e:
                    print(f"⚠️ Eroare la conversia prețului pentru link-ul {product_link}: {e}")
                    continue
                
        print(f"✅ [ATVROM] Am parsat și calculat TVA pentru {len(price_map)} produse.")
        return price_map
        
    except requests.exceptions.RequestException as e:
        print(f"❌ [ATVROM] Eroare la descărcarea XML: {e}")
        return {}
    except ET.ParseError as e:
        print(f"❌ [ATVROM] Eroare la parsarea XML: {e}")
        return {}

if __name__ == '__main__':
    # Exemplu de test
    price_map = get_atvrom_price_map()
    # print(price_map)
    
    # Testarea prețului: 27553 * 1.21 = 33339.13
    test_link = "https://www.atvrom.ro/motociclete/kawasaki-z500-se"
    if test_link in price_map:
        print(f"Test: Preț calculat pentru {test_link}: {price_map[test_link]}")
    else:
        print("Test: Link-ul de test nu a fost găsit în harta prețurilor.")
