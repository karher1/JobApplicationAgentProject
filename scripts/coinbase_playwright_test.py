from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Set headless=True for no UI
    page = browser.new_page()
    page.goto("https://www.coinbase.com/careers/positions")
    input("Press Enter after you see the page (and solve any CAPTCHA if present)...")
    # Save the HTML after manual interaction
    html = page.content()
    with open("coinbase_careers.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML saved to coinbase_careers.html")
    browser.close() 