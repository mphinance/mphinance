from playwright.sync_api import sync_playwright
import time

def run():
    print("Launching playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1100, "height": 950})
        
        url = "file:///home/sam/mphinance/docs/widgets/10-year-engine-calculator.html"
        print(f"Loading {url}")
        page.goto(url)
        
        # Wait for the JS to inject the DOM elements
        page.wait_for_timeout(2000)
        
        output_path = "/home/sam/mphinance/docs/substack/assets/calculator_screenshot.png"
        page.screenshot(path=output_path, full_page=False)
        print(f"Screenshot saved to {output_path}")
        browser.close()

if __name__ == "__main__":
    run()
