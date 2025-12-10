import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import requests
# --- IMPORTURI PENTRU EMAIL ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURARE EMAIL (SCHIMBĂ VALORILE CU DATELE TALE) ---
SENDER_EMAIL = 'mihaistoian889@gmail.com'
RECEIVER_EMAIL = 'octavian@atvrom.ro'
SMTP_PASSWORD = 'igcu wwbs abit ganm'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
# ------------------------------------------------------------

# ⚠️ Aceste funcții sunt necesare DOAR pentru competitori.
# Funcțiile pentru ATVROM (get_atvrom_price_map, process_atvrom_link) au fost eliminate.
from monitor.sites.evo_moto import scrape_evomoto
from monitor.sites.moto4all import scrape_moto4all_prices
from monitor.sites.motoboom import scrape_motoboom_prices
from monitor.sites.motomus import get_motomus_price
from monitor.sites.moto24 import scrape_moto24
from monitor.sites.jetskiadrenalin import get_jetskiadrenalin_price

# ----------------------------------------------------
## 1\. ⚙️ Configurare Globală și Harta de Coordonate

# --- Foaia de Calcul ---
SPREADSHEET_NAME = 'Price Monitor ATVRom'
WORKSHEET_NAME = 'Can-Am'
CREDENTIALS_FILE = 'service_account_credentials.json'

# Harta: { Index Coloană Sursă (Link): [Index Coloană Destinație (Preț), Funcție Scraper] }
# Am ELIMINAT logica ATVROM (B -> I). Scriptul se ocupă acum doar de competitori (C-H -> J-O).
# Coloana A = Index 1, B = 2, I = 9, O = 15, P = 16
SCRAPER_COORDS = {
    3: [10, scrape_evomoto],                # C -> J (Evo-Moto)
    4: [11, scrape_moto4all_prices],        # D -> K (Moto4all)
    5: [12, scrape_motoboom_prices],        # E -> L (Motoboom)
    6: [13, get_motomus_price],             # F -> M (Motomus)
    7: [14, scrape_moto24],                 # G -> N (Moto24)
    8: [15, get_jetskiadrenalin_price],     # H -> O (JetskiAdrenalin)
}

# Coloana pentru Timestamp-ul general (Coloana P)
TIMESTAMP_COL_INDEX = 16

def get_public_ip():
    # Funcția menținută pentru diagnosticare în log-uri
    response = requests.get('https://ifconfig.me/ip', timeout=5)
    if response.status_code == 200:
        return response.text.strip()
    return "N/A (Eroare de raspuns)"

# ----------------------------------------------------
## 2\. 🔑 Funcțiile de Conexiune și Alertă (Neschimbate)

def setup_sheets_client():
    """Inițializează clientul gspread și returnează foaia de lucru."""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        # Folosește credențialele din fișierul JSON
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        
        # Deschide foaia de calcul și foaia de lucru
        spreadsheet = client.open(SPREADSHEET_NAME)
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        print(f"✅ Conexiune reușită la foaia de lucru '{WORKSHEET_NAME}'.")

        current_ip = get_public_ip()
        print(f"🌐 IP-ul public de ieșire al Runner-ului: **{current_ip}**")
        
        return sheet
    except Exception as e:
        print(f"❌ Eroare la inițializarea Google Sheets client: {e}")
        print("Asigură-te că fișierul JSON există și că adresa de email a robotului este partajată cu foaia.")
        return None
    
def send_alert_email(subject, body):
    """Trimite un email folosind SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        # Folosim HTML pentru a formata tabelul de alerte
        msg.attach(MIMEText(body, 'html')) 

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✔️ Notificare trimisă cu succes către {RECEIVER_EMAIL}")
        return True
    except Exception as e:
        print(f"❌ Eroare la trimiterea email-ului: {e}")
        print("Verifică setările SMTP_PASSWORD și permisiunile contului.")
        return False
    
def send_price_alerts(sheet):
    """
    Citește coloanele de diferență (Q-V) și trimite o notificare
    dacă găsește diferențe negative (concurentul are preț mai mic).
    Această funcție se bazează pe faptul că prețul ATVROM (I) și prețurile competitorilor (J-O)
    sunt deja actualizate.
    """
    if sheet is None:
        return

    try:
        # Citim datele de la Rândul 2 în jos.
        all_data = sheet.get_all_values()[1:] 
        
    except Exception as e:
        print(f"❌ Eroare la citirea datelor pentru alertă: {e}")
        return

    alert_products = [] 
    
    # Numele site-urilor corespunzător Coloanelor de Diferență (Q la V)
    COMPETITOR_NAMES = ["Evo-Moto", "Moto4all", "Motoboom", "Motomus", "Moto24", "JetskiAdrenalin"]
    
    # Prețul ATVROM (din Apps Script/VLOOKUP) se află pe indexul 8 (Coloana I)
    YOUR_PRICE_COL_INDEX = 8         
    FIRST_DIFFERENCE_INDEX = 16  # Index Q (Coloana Q este la indexul 16)
    
    for row_data in all_data:
        # Ne asigurăm că există date
        if not row_data or len(row_data) < (FIRST_DIFFERENCE_INDEX + len(COMPETITOR_NAMES)):
            continue
            
        product_name = row_data[0]
        # Prețul ATVROM (scris în coloana I)
        your_price_str = row_data[YOUR_PRICE_COL_INDEX] 
        
        competitor_alerts = [] 
        
        # Iterăm prin cele 6 coloane de diferență (Q la V)
        for i in range(len(COMPETITOR_NAMES)):
            difference_index = FIRST_DIFFERENCE_INDEX + i
            competitor_name = COMPETITOR_NAMES[i]
            
            try:
                # Citim valoarea (va fi un string gol "" sau un număr negativ)
                diff_value_str = row_data[difference_index]
                
                if diff_value_str and diff_value_str.strip() != "":
                    # Convertim valoarea din Sheets (ex: 1.234,56) la float Python (ex: 1234.56)
                    # Presupunem că formula Sheets returnează numărul formatat (ex: 1.234,56)
                    # Aici, presupunem că Sheets returnează valorile numerice (din formula IF)
                    # folosind separatorul zecimal local (virgulă pentru RON)
                    
                    # Încercăm o conversie simplă (care funcționează dacă Sheets returnează doar zecimale cu punct)
                    # Dacă Sheets returnează "1,234.00" sau "-1.23", se bazează pe setările regionale.
                    # Rămânem la logica care funcționează pentru separatori:
                    difference = float(diff_value_str.replace(",", ".")) 
                    
                    # Dacă am citit o valoare, ea este negativă (datorită formulei IF din Sheets)
                    # care apare doar dacă prețul competitorului (J,K,L,M,N,O) este mai mic decât I.
                    competitor_alerts.append({
                        'name': competitor_name,
                        # Luăm valoarea absolută (diferența pozitivă)
                        'difference': abs(difference) 
                    })
                        
            except (ValueError, IndexError, TypeError):
                continue

        if competitor_alerts:
            alert_products.append({
                'product': product_name,
                'your_price': your_price_str,
                'alerts': competitor_alerts
            })

    # --- Generarea și Trimiterea Email-ului ---
    if alert_products:
        
        email_body = "Bună ziua,<br><br>Am detectat următoarele prețuri **mai mici la concurență**:<br>"
        email_body += "<table border='1' cellpadding='8' cellspacing='0' style='width: 70%; border-collapse: collapse; font-family: Arial;'>"
        email_body += "<tr style='background-color: #f2f2f2; font-weight: bold;'><th>Produs</th><th>Prețul Tău (RON)</th><th>Concurent</th><th>Diferență (RON)</th></tr>"
        
        for product_alert in alert_products:
            is_first_alert = True
            for alert in product_alert['alerts']:
                if is_first_alert:
                    row_span = len(product_alert['alerts'])
                    email_body += f"<tr>"
                    # Numele produsului și prețul tău se întind pe rândurile alertei
                    email_body += f"<td rowspan='{row_span}'><b>{product_alert['product']}</b></td>"
                    email_body += f"<td rowspan='{row_span}' style='color: green;'>{product_alert['your_price']}</td>"
                    is_first_alert = False
                else:
                    email_body += f"<tr>"
                    
                email_body += f"<td>{alert['name']}</td>"
                # Afișăm diferența în format monetar, pozitiv, evidențiind economia pe care o face concurentul
                email_body += f"<td style='color: red; font-weight: bold;'>{alert['difference']:.2f} RON mai mic</td>" 
                email_body += f"</tr>"

        email_body += "</table>"
        email_body += "<br>Vă rugăm să revizuiți strategia de preț."
        
        subject = f"🚨 [ALERTĂ PREȚ] {len(alert_products)} Produse Can-Am cu Preț Mai Mic la Concurență"
        
        send_alert_email(subject, email_body) 

    else:
        print("\n✅ Nu s-au găsit produse cu prețuri mai mici la concurență.")

# ----------------------------------------------------
## 3\. 🔄 Funcția de Monitorizare și Actualizare (Doar Competitori)

def monitor_and_update_sheet(sheet):
    """Citește link-urile competitorilor, extrage prețurile și actualizează coloanele J-O."""
    if sheet is None:
        print("Oprire. Foaia de lucru nu a putut fi inițializată.")
        return

    print(f"\n--- 1. Prețul ATVROM (Coloana I) este preluat de Apps Script/Formule. Scriptul se ocupă doar de competitori. ---")

    # Citim toate datele de la rândul 2 în jos (excludem antetul)
    try:
        all_data = sheet.get_all_values()[1:] 
    except Exception as e:
        print(f"❌ Eroare la citirea datelor din foaie: {e}")
        return

    updates = []
    timestamp_val = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"\n--- 2. Începe procesarea a {len(all_data)} produse ---")

    # Parcurgem fiecare rând (produs)
    for row_index, row_data in enumerate(all_data):
        gsheet_row_num = row_index + 2 
        product_name = row_data[0] 

        print(f"\n➡️ Procesează: {product_name} la rândul {gsheet_row_num}")

        # Parcurgem harta de coordonate (doar competitori)
        for src_col_idx, (dest_col_idx, extractor_func) in SCRAPER_COORDS.items():
            
            link_index_in_list = src_col_idx - 1 
            
            # Verificăm dacă există link în coloana sursă (C, D, E, F, G, sau H)
            if link_index_in_list < len(row_data) and row_data[link_index_in_list]:
                url = row_data[link_index_in_list]
                scraper_name = url.split('/')[2] 

                dest_col_letter = gspread.utils.rowcol_to_a1(1, dest_col_idx).split('1')[0]
                cell_range = f'{dest_col_letter}{gsheet_row_num}'
                price = None
                
                # --- LOGICĂ PENTRU COMPETITORI - SE FACE SCRAPING ---
                print(f"    - Scrapează {scraper_name}...")
                try:
                    price = extractor_func(url)
                    
                    if price is not None:
                        # Formatează prețul la 2 zecimale
                        price_str = f"{price:.2f}"
                        print(f"      ✅ Succes: {price_str} RON. Scris la {cell_range}")
                    else:
                        price_str = "N/A (SCRAPE ESUAT)"
                        print(f"      ❌ EROARE: Extragerea prețului a eșuat (returnat None) pentru {scraper_name}.")
                        price = price_str # pentru a adăuga mesajul de eroare în updates
                        
                except Exception as e:
                    price_str = f"🛑 EXCEPȚIE ({type(e).__name__})"
                    print(f"      🛑 EXCEPȚIE la scraping pentru {scraper_name}: {e}")
                    price = price_str
                    
                time.sleep(1) # Pauză de 1 secundă între fiecare cerere de scraping (pentru competitori)
                
                
                # --- Adăugare la lista de actualizări ---
                if price is not None:
                    # Dacă prețul este un float/int, îl convertim în string pentru a fi scris.
                    if isinstance(price, (float, int)):
                            price = f"{price:.2f}"
                            
                    updates.append({
                        'range': cell_range,
                        'values': [[price]]
                    })


    # ----------------------------------------
    # Scrierea Batch în Google Sheets (la final)
    
    # Adaugă timestamp-ul final în coloana P pentru toate rândurile procesate
    if updates:
        
        # Determinăm litera coloanei P
        timestamp_col_letter = gspread.utils.rowcol_to_a1(1, TIMESTAMP_COL_INDEX).split('1')[0] 
        
        # Rândul începe de la 2 și se termină la (len(all_data) + 1)
        timestamp_range = f'{timestamp_col_letter}2:{timestamp_col_letter}{len(all_data) + 1}'
        
        # Creează o listă de liste pentru a scrie aceeași valoare pe toate rândurile
        timestamp_values = [[timestamp_val] for _ in all_data]
        
        updates.append({
            'range': timestamp_range,
            'values': timestamp_values
        })
        
        print(f"\n⚡ Se scriu {len(updates)} actualizări și timestamp-ul ({timestamp_val}) în foaie...")
        
        try:
            # Atenție: Acum actualizăm doar coloanele J-O și P.
            sheet.batch_update(updates)
            print("🎉 Toate prețurile competitorilor și timestamp-ul au fost actualizate cu succes!")
        except Exception as e:
            print(f"❌ EROARE la scrierea în foaia de calcul: {e}")
    else:
        print("\nNu au fost găsite prețuri noi de actualizat.")


# ----------------------------------------------------
## 4\. 🏁 Punctul de Intrare

if __name__ == "__main__":
    # 1. Inițializează conexiunea
    sheet_client = setup_sheets_client()
    
    if sheet_client:
        # 2. Rulează monitorizarea și actualizarea foii (Această funcție actualizează coloanele J-O)
        monitor_and_update_sheet(sheet_client)
        
        # 3. Odată ce foaia este actualizată, rulează logica de alertare
        # care citește din foaie (I, Q-V)
        send_price_alerts(sheet_client)
