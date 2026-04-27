from playwright.sync_api import sync_playwright

URL = "https://evo-moto.ro/kawasaki-vulcan-s-2026"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False,
        args=["--disable-blink-features=AutomationControlled"])
    
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )

    page = context.new_page()

    print(">>> Navigating...")
    page.goto(URL, timeout=60000, wait_until="domcontentloaded")

    # Așteptăm 8 secunde
    page.wait_for_timeout(8000)

    html = page.content()

    print("\n========== HTML PRIMIT ==========\n")
    print(html[:5000])  # afișăm primele 5000 caractere
    print("\n=================================\n")

    browser.close()
