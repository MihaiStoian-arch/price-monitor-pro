from monitor.sites.evo_moto import scrape_evomoto

url = "https://evo-moto.ro/kawasaki-vulcan-s-2026"
print("Preț EVO MOTO:", scrape_evomoto(url))
