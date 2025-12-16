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
RECEIVER_EMAILS = [
    'octavian@atvrom.ro',
    'svmitza89@gmail.com'
]
SMTP_PASSWORD = 'igcu wwbs abit ganm'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
# ------------------------------------------------------------

# Pragul minim de diferență (în RON) sub care nu se trimite alertă
# CORECȚIA CRITICĂ: Definit la nivel global pentru a evita NameError
MINIMUM_DIFFERENCE_THRESHOLD = 1.0 

# ⚠️ Asigură-te că funcțiile de scraping sunt importate corect din directorul monitor/sites
from monitor.sites.evo_moto import scrape_evomoto
from monitor.sites.moto4all import scrape_moto4all_prices
from monitor.sites.motoboom import scrape_motoboom_prices
from monitor.sites.motomus import get_motomus_price
from monitor.sites.moto24 import scrape_moto24
from monitor.sites.jetskiadrenalin import get_jetskiadrenalin_price

# ----------------------------------------------------
## 1. ⚙️ Configurare Globală și Harta de Coordonate

# --- Foaia de Calcul ---
SPREADSHEET_NAME = 'Price Monitor ATVRom'
WORKSHEET_NAME = 'Can-Am'
CREDENTIALS_FILE = 'service_account_credentials.json'

# Harta: { Index Coloană Sursă (Link): [Index Coloană Destinație (Preț), Funcție Scraper] }
# Coloana A = 1, I = 9, P = 16
# Scriptul se ocupă doar de competitori (C-H -> J-O).
SCRAPER_COORDS = {
    3: [10, scrape_evomoto],            # C -> J (Evo-Moto)
    4: [11, scrape_moto4all_prices],    # D -> K (Moto4all)
    5: [12, scrape_motoboom_prices],    # E -> L (Motoboom)
    6: [13, get_motomus_price],         # F -> M (Motomus)
    7: [14, scrape_moto24],             # G -> N (Moto24)
    8: [15, get_jetskiadrenalin_price], # H -> O (JetskiAdrenalin)
}

# Coloana pentru Timestamp-ul general (Coloana P)
TIMESTAMP_COL_INDEX = 16

def get_public_ip():
    """Funcția menținută pentru diagnosticare în log-uri."""
    try:
        response = requests.get('https://ifconfig.me/ip', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return "N/A (Eroare de raspuns)"
    except requests.exceptions.RequestException:
        return "N/A (Eroare de retea)"

# ----------------------------------------------------
## 2. 🔑 Funcțiile de Conexiune și Alertă

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
        receiver_string = ", ".join(RECEIVER_EMAILS)
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_string # Folosim șirul de caractere (string) aici
        msg['Subject'] = subject
        # Folosim HTML
        msg.attach(MIMEText(body, 'html')) 

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls() # Secure the connection
        server.login(SENDER_EMAIL, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        server.quit()
        print(f"✔️ Notificare trimisă cu succes către {RECEIVER_EMAILS}")
        return True
    except Exception as e:
        print(f"❌ Eroare la trimiterea email-ului: {e}")
        print("Verifică setările SMTP_PASSWORD și permisiunile contului.")
        return False
    
def send_price_alerts(sheet):
    """
    Citește coloanele de diferență (Q-V) și trimite o notificare
    dacă găsește diferențe negative (concurentul are preț mai mic)
    și dacă diferența absolută depășește pragul MINIMUM_DIFFERENCE_THRESHOLD.
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
    
    YOUR_PRICE_INDEX = 8         # Index I
    FIRST_DIFFERENCE_INDEX = 16  # Index Q (Coloana Q este la indexul 16)
    
    for row_data in all_data:
        # Ne asigurăm că există date și că numele produsului nu este gol
        if not row_data or len(row_data) < (FIRST_DIFFERENCE_INDEX + len(COMPETITOR_NAMES)):
            continue
            
        product_name = row_data[0]
        # Prețul ATVROM (din I), folosit doar în email
        your_price_str = row_data[YOUR_PRICE_INDEX] 
        
        competitor_alerts = [] 
        
        # Iterăm prin cele 6 coloane de diferență (Q la V)
        for i in range(len(COMPETITOR_NAMES)):
            difference_index = FIRST_DIFFERENCE_INDEX + i
            competitor_name = COMPETITOR_NAMES[i]
            
            try:
                # Citim valoarea (va fi un string gol "" sau o valoare numerică negativă)
                diff_value_str = row_data[difference_index]
                
                if diff_value_str and diff_value_str.strip() != "":
                    # Sheets returnează numerele formatate regional. Python are nevoie de '.' ca separator
                    difference = float(diff_value_str.replace(",", ".")) 
                    
                    # LOGICA CORECTATĂ: Alerta se declanșează DOAR dacă valoarea este negativă ȘI depășește pragul MINIMUM_DIFFERENCE_THRESHOLD.
                    if difference < 0 and abs(difference) >= MINIMUM_DIFFERENCE_THRESHOLD:
                        competitor_alerts.append({
                            'name': competitor_name,
                            # Stocăm valoarea absolută (diferența pozitivă) pentru afișarea în email
                            'difference': abs(difference) 
                        })
                        
            except (ValueError, IndexError, TypeError):
                # Ignoră celulele care nu sunt numere valide (ex: #VALUE!, N/A, string gol)
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
                # Rotunjirea la întreg (:.0f) este menținută
                email_body += f"<td style='color: red; font-weight: bold;'>{alert['difference']:.0f} RON mai mic</td>" 
                email_body += f"</tr>"

        email_body += "</table>"
        email_body += "<br>Vă rugăm să revizuiți strategia de preț."
        
        subject = f"🚨 [ALERTĂ PREȚ] {len(alert_products)} Produse Can-Am cu Preț Mai Mic la Concurență"
        
        send_alert_email(subject, email_body) 

    else:
        print("\n✅ Nu s-au găsit produse cu prețuri mai mici la concurență.")

# ----------------------------------------------------
## 3. 🔄 Funcția de Monitorizare și Actualizare (Doar Competitori)

def monitor_and_update_sheet(sheet):
    """Citește link-urile competitorilor (C-H), extrage prețurile și actualizează coloanele J-O."""
    if sheet is None:
        print("Oprire. Foaia de lucru nu a putut fi inițializată.")
        return

    print(f"\n--- 1. Scriptul actualizează doar prețurile competitorilor (J-O) și timestamp-ul (P). ---")

    # Citim toate datele de la rândul 2 în jos (excludem antetul)
    try:
        all_data = sheet.get_all_values()[1:]
    except Exception as e:
        print(f"❌ Eroare la citirea datelor din foaie: {e}")
        return

    updates = [] # Initializare corectă
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
                        # Formatează prețul la 2 zecimale (ex: "72908.55")
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
            # ADĂUGAREA CRITICĂ AICI: USER_ENTERED (păstrată din codul original al dvs.)
            sheet.batch_update(updates, value_input_option='USER_ENTERED')
            print("🎉 Toate prețurile competitorilor și timestamp-ul au fost actualizate cu succes!")
        except Exception as e:
            print(f"❌ EROARE la scrierea în foaia de calcul: {e}")
    else:
        print("\nNu au fost găsite prețuri noi de actualizat.")


# ----------------------------------------------------
## 4. 🏁 Punctul de Intrare

if __name__ == "__main__":
    # 1. Inițializează conexiunea
    sheet_client = setup_sheets_client()
    
    if sheet_client:
        # 2. Rulează monitorizarea și actualizarea foii (Această funcție actualizează coloanele J-O)
        monitor_and_update_sheet(sheet_client)
        
        # 3. Odată ce foaia este actualizată, rulează logica de alertare
        send_price_alerts(sheet_client)
