from monitor.sites.atvrom import scrape_atvrom

URL = "https://atvrom.ro/motociclete/cfmoto-125nk-abs-25"

price = scrape_atvrom(URL)
print("Preț găsit:", price)
