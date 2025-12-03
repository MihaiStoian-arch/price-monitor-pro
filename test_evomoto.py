from monitor.sites.evo_moto import scrape_evomoto

URL = "https://evo-moto.ro/kawasaki-vulcan-s-2026"

price = scrape_evomoto(URL)
print("Preț EVOMOTO:", price)
