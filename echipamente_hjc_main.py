import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import requests
import os
import re
from dotenv import load_dotenv

# --- IMPORTURI PENTRU EMAIL ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ⚠️ IMPORTĂRILE FUNCȚIILOR DE SCRAPING
# Presupunem ca acestea sunt in locatiile corecte: monitor.sites.pga_nordicamoto si monitor.sites.pga_moto24
from monitor.sites.pga_nordicamoto import scrape_nordicamoto_search
from monitor.sites.pga_moto24 import scrape_moto24_search

load_dotenv()

# --- CONFIGURARE EMAIL (din .env) ---
SENDER_EMAIL = os.environ['SENDER_EMAIL']
# Lista de destinatari (CSV in .env: RECEIVER_EMAILS=a@x,b@y,c@z)
RECEIVER_EMAILS = [e.strip() for e in os.environ['RECEIVER_EMAILS'].split(',') if e.strip()]
SMTP_PASSWORD = os.environ['SMTP_PASSWORD']
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
# ------------------------------------------------------------

# Pragul minim de diferență (în RON) sub care nu se trimite alertă
MINIMUM_DIFFERENCE_THRESHOLD = 1.0

# ----------------------------------------------------
## 1. ⚙️ Configurare Globală și Harta de Coordonate 

# --- Foaia de Calcul ---
SPREADSHEET_NAME = 'Price Monitor ATVRom'
WORKSHEET_NAME = 'Echipamente HJC'
CREDENTIALS_FILE = 'service_account_credentials.json'

# Coloanele relevante (indexarea începe de la 1):
# A=1 (Titlu Produs), B=2 (Cod Produs), C=3 (Preț ATVROM), 
# D=4 (Preț Moto24), E=5 (Preț Nordicamoto), F=6 (Data Scrape)
# G=7 (Diferența Moto24), H=8 (Diferența Nordicamoto)

# Harta: Folosim doar pentru referință (Nota: Structura ar trebui să fie un dicționar cu chei unice)
# SCRAPER_COORDS = { ... } # Lăsat așa cum este, dar nu este folosit în logica actuală

# Coloana pentru Timestamp-ul (Coloana F)
TIMESTAMP_COL_INDEX = 6

# Indicii pentru Coloane în lista de date (indexarea începe de la 0):
COD_PRODUS_INDEX = 1        # Coloana B
TITLE_PRODUS_INDEX = 0      # Coloana A
LAST_PRICE_ATVROM_INDEX = 2 # Coloana C
PRICE_MOTO24_INDEX = 3      # Coloana D
PRICE_NORDICAMOTO_INDEX = 4 # Coloana E
DIFFERENCE_MOTO24_INDEX = 6 # Coloana G (pentru alerte)
DIFFERENCE_NORDICAMOTO_INDEX = 7 # Coloana H (pentru alerte)


def clean_and_convert_price(price_text):
    if not price_text:
        return None
    
    # Curățare inițială (Lei/RON, spații)
    price_text = price_text.upper().replace('LEI', '').replace('RON', '').replace(' ', '').strip()

    # Elimină caracterele non-numerice/non-separator
    price_text = re.sub(r'[^\d.,]', '', price_text)
    
    # --- LOGICA NOUĂ PENTRU SEPARATOARE ---
    # 1. Dacă textul CONȚINE virgulă, tratăm punctul ca separator de mii.
    if ',' in price_text:
        price_text = price_text.replace('.', '')
        # Standardizăm separatorul zecimal la punct
        cleaned_price_str = price_text.replace(',', '.')
    
    # 2. Dacă textul NU CONȚINE virgulă, dar CONȚINE punct, tratăm punctul ca separator de mii.
    elif '.' in price_text:
        cleaned_price_str = price_text.replace('.', '')
    
    # 3. Fără separatori, doar cifre.
    else:
        cleaned_price_str = price_text

    # --- CONVERSIE FINALĂ ---
    try:
        if cleaned_price_str:
            return float(cleaned_price_str)
        return None
    except ValueError:
        return None


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
    """Trimite un email folosind SMTP. CORECTAT: Gestionează lista de destinatari."""
    try:
        # CORECTIE 1: Formatăm lista de email-uri ca un șir de caractere separat prin virgulă pentru antetul 'To:'
        receiver_string = ", ".join(RECEIVER_EMAILS)
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_string # Folosim șirul de caractere (string) aici
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html')) 

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SMTP_PASSWORD) 
        
        # CORECTIE 2: Folosim lista originală (list) pentru funcția sendmail, care o acceptă
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAILS, msg.as_string())
        
        server.quit()
        print(f"✔️ Notificare trimisă cu succes către {receiver_string}")
        return True
    except Exception as e:
        print(f"❌ Eroare la trimiterea email-ului: {e}")
        print("Verifică setările SMTP_PASSWORD și permisiunile contului.")
        return False
    
def send_price_alerts(sheet):
    """
    Citește coloanele de diferență (G și H) calculate de formulele din foaie
    și trimite o notificare dacă găsește diferențe negative care depășesc pragul.
    """
    if sheet is None:
        return

    print("\n--- 3. Verificare Alerte (Citire Coloane G și H) ---")
    try:
        # Citim toate datele necesare (A-H). Presupunem că citim până la H (index 7)
        all_data = sheet.get_all_values()[1:]  
    except Exception as e:
        print(f"❌ Eroare la citirea datelor pentru alertă: {e}")
        return

    alert_products = [] 
    
    DIFFERENCE_COLUMNS = [
        (DIFFERENCE_MOTO24_INDEX, "Moto24", PRICE_MOTO24_INDEX), 
        (DIFFERENCE_NORDICAMOTO_INDEX, "Nordicamoto", PRICE_NORDICAMOTO_INDEX)
    ]
    
    # Rămâne neschimbat: Codul Produsului este extras și inclus în alert_products
    PRODUCT_CODE_INDEX = 1 

    for row_data in all_data:
        
        if not row_data or len(row_data) < 8: 
            continue
            
        product_title = row_data[TITLE_PRODUS_INDEX] 
        product_code = row_data[PRODUCT_CODE_INDEX]   
        atvrom_price_str = row_data[LAST_PRICE_ATVROM_INDEX]
        
        for diff_index, competitor_name, price_index in DIFFERENCE_COLUMNS:
            
            diff_value_str = row_data[diff_index]
            
            try:
                if diff_value_str and diff_value_str.strip() != "":
                    difference = float(diff_value_str.replace(",", ".")) 
                    
                    if difference < 0 and abs(difference) >= MINIMUM_DIFFERENCE_THRESHOLD:
                        
                        competitor_price_str = row_data[price_index]
                        
                        alert_products.append({
                            'product': product_title,
                            'code': product_code,  # Păstrat: Codul Produsului
                            'your_price': atvrom_price_str,
                            'competitor': competitor_name,
                            'competitor_price': competitor_price_str,
                            'difference': abs(difference) 
                        })
                        
            except (ValueError, IndexError, TypeError):
                continue

    # --- Generarea și Trimiterea Email-ului ---
    if alert_products:
        
        email_body = "Bună ziua,<br><br>Am detectat următoarele prețuri **mai mici la concurență**:<br>"
        email_body += "<table border='1' cellpadding='8' cellspacing='0' style='width: 90%; border-collapse: collapse; font-family: Arial;'>"
        
        # Păstrat: Antetul tabelului include Codul
        email_body += "<tr style='background-color: #f2f2f2; font-weight: bold;'><th>Produs (Cod)</th><th>Prețul Tău (C)</th><th>Concurent</th><th>Prețul Concurent (D/E)</th><th>Diferență (RON)</th></tr>"
        
        for alert in alert_products:
            email_body += f"<tr>"
            
            # Păstrat: Includerea Codului sub Numele Produsului
            email_body += f"<td><b>{alert['product']}</b><br><span style='font-size: 0.9em;'>({alert['code']})</span></td>" 
            
            email_body += f"<td style='color: green;'>{alert['your_price']}</td>"
            email_body += f"<td>{alert['competitor']}</td>"
            email_body += f"<td style='color: red;'>{alert['competitor_price']}</td>"
            email_body += f"<td style='color: red; font-weight: bold;'>{alert['difference']:.0f} RON mai mic</td>" 
            email_body += f"</tr>"

        email_body += "</table>"
        email_body += "<br>Vă rugăm să revizuiți strategia de preț."
        
        subject = f"🚨 [ALERTĂ PREȚ] {len(alert_products)} Produse HJC cu Preț Mai Mic la Concurență"
        
        send_alert_email(subject, email_body) 

    else:
        print("\n✅ Nu s-au găsit produse cu prețuri mai mici la concurență.")


# ----------------------------------------------------
## 3. 🔄 Funcția de Monitorizare și Actualizare

def monitor_and_update_sheet(sheet):
    """Citește codurile de produs (B), extrage prețurile (D și E) și actualizează coloana F."""
    if sheet is None:
        print("Oprire. Foaia de lucru nu a putut fi inițializată.")
        return

    print(f"\n--- 1. Scriptul actualizează prețurile Moto24 (D) și Nordicamoto (E), și timestamp-ul (F). ---")

    try:
        # Citim datele de la rândul 2 în jos (excludem antetul)
        all_data = sheet.get_all_values()[1:] 
    except Exception as e:
        print(f"❌ Eroare la citirea datelor din foaie: {e}")
        return

    updates = []
    timestamp_val = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"\n--- 2. Începe procesarea a {len(all_data)} produse ---")

    for row_index, row_data in enumerate(all_data):
        gsheet_row_num = row_index + 2
        
        product_code = row_data[COD_PRODUS_INDEX].strip()

        if not product_code:
             print(f"➡️ Rândul {gsheet_row_num} ignorat (Cod Produs gol).")
             continue

        print(f"\n➡️ Procesează: Codul {product_code} la rândul {gsheet_row_num}")
        
        scraper_info = [
            (scrape_moto24_search, 4),      # Moto24 (Coloana D)
            (scrape_nordicamoto_search, 5)  # Nordicamoto (Coloana E)
        ]
        
        row_updates = [None] * 2
        
        # Iterăm prin cele două scrape-uri necesare: D (Moto24) și E (Nordicamoto)
        for i, (scraper_func, col_index) in enumerate(scraper_info):
            site_name = "Moto24" if col_index == 4 else "Nordicamoto"
            
            print(f"  - Scrapează {site_name}...")
            try:
                # Se presupune că funcțiile de scraping (din import) acceptă și funcția de curățare
                price_float = scraper_func(product_code, clean_and_convert_price) 
                
                if price_float is not None:
                    # Asigurăm formatarea corectă pentru GSheets
                    price_str = f"{price_float:.2f}"
                    print(f"    ✅ Succes {site_name}: {price_str} RON.")
                else:
                    price_str = "N/A (SCRAPE ESUAT)"
                    print(f"    ❌ EROARE {site_name}: Extragerea prețului a eșuat (returnat None).")
                    
                row_updates[i] = price_str
            except Exception as e:
                row_updates[i] = f"🛑 EXCEPȚIE ({type(e).__name__})"
                print(f"    🛑 EXCEPȚIE {site_name}: {e}")
            
            time.sleep(1) 
        
        # --- Adăugare la lista de actualizări D și E (într-un singur apel) ---
        range_d_e = f'{gspread.utils.rowcol_to_a1(gsheet_row_num, 4)}:{gspread.utils.rowcol_to_a1(gsheet_row_num, 5)}'
        
        updates.append({
            'range': range_d_e,
            'values': [row_updates] # Scrie lista [Pret D, Pret E] pe rândul respectiv
        })


    # ----------------------------------------
    # Scrierea Batch în Google Sheets (la final)
    
    if updates:
        
        # Adaugă timestamp-ul final în coloana F (index 6) pentru toate rândurile procesate
        timestamp_col_letter = gspread.utils.rowcol_to_a1(1, TIMESTAMP_COL_INDEX).split('1')[0] 
        timestamp_range = f'{timestamp_col_letter}2:{timestamp_col_letter}{len(all_data) + 1}'
        timestamp_values = [[timestamp_val] for _ in all_data]
        
        updates.append({
            'range': timestamp_range,
            'values': timestamp_values
        })
        
        print(f"\n⚡ Se scriu {len(updates)} actualizări și timestamp-ul ({timestamp_val}) în foaie...")
        
        try:
            sheet.batch_update(updates, value_input_option='USER_ENTERED')
            print("🎉 Toate prețurile și timestamp-ul au fost actualizate cu succes!")
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
        # 2. Rulează monitorizarea și actualizarea foii (D, E, F)
        monitor_and_update_sheet(sheet_client)
        
        # 3. Odată ce foaia este actualizată, rulează logica de alertare (G, H)
        # Pauză de 5 secunde pentru a permite formulelor G și H să se recalculeze în Sheets
        time.sleep(5) 
        send_price_alerts(sheet_client)
