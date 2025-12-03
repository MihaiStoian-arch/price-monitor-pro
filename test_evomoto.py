from monitor.sites.evo_moto import scrape_evomoto

url = "https://evo-moto.ro/kawasaki-vulcan-s-2026"

price = scrape_evomoto(url)
print("Preț EVOMOTO:", price)
