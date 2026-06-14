import asyncio
import os
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ==========================================
# ⚙️ CONFIGURATION SECTION
# ==========================================
TARGET_URL = "https://www.amazon.in/gp/bestsellers"      # The starting URL
MAX_DEPTH = 1                           # 0 = Main page only, 1 = Main page + its sub-links
OUTPUT_FILE = "data.md"                 # Where the scraped text will be saved

# --- PAGINATION SETTINGS ---
# Set to 'scroll', 'button', or 'none' depending on the target website
PAGINATION_MODE = 'none'                

# If using 'button' mode, you MUST update this CSS selector to match the target site!
# Examples: ".next-page", "button#load-more", "a.pagination-next"
NEXT_BUTTON_SELECTOR = ".next-page"     
# ==========================================

# Track visited URLs globally to prevent infinite loops
visited_urls = set()

async def human_delay(min_s=1.5, max_s=4.0):
    """Introduces a randomized delay to bypass behavioral WAF detection."""
    await asyncio.sleep(random.uniform(min_s, max_s))

def extract_and_save_text(html_content, url, current_depth, title):
    """Uses Beautiful Soup to clean the HTML and save raw text to a Markdown file."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove structural noise (menus, scripts, styles, footers)
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        element.decompose()
    
    # Extract clean human-readable text
    clean_text = soup.get_text(separator="\n", strip=True)

    # Append to the data.md file
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n# URL: {url}\n")
        f.write(f"## Title: {title}\n")
        f.write(f"### Depth Level: {current_depth}\n")
        f.write(f"---\n\n{clean_text}\n")
        f.write("\n" + "="*50 + "\n")

async def handle_infinite_scroll(page):
    """Scrolls to the bottom of a dynamically loading page until it stops growing."""
    print("Initiating infinite scroll...")
    last_height = await page.evaluate("document.body.scrollHeight")
    
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await human_delay(2.5, 4.5) # Wait for network requests to fetch new items
        
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            print("Reached the bottom of the infinite scroll.")
            break
        last_height = new_height

async def handle_button_pagination(page):
    """Clicks the 'Next' button repeatedly until it disappears."""
    print("Initiating button pagination...")
    page_num = 1
    
    while True:
        await human_delay(2.0, 4.0)
        button = page.locator(NEXT_BUTTON_SELECTOR)
        
        if await button.count() > 0 and await button.is_visible():
            print(f"Clicking 'Next' button to load page {page_num + 1}...")
            await button.click()
            await page.wait_for_load_state("domcontentloaded")
            page_num += 1
        else:
            print("No more 'Next' button found. Pagination complete.")
            break

async def scrape_page(page, url, current_depth, base_domain):
    """Core recursive function to navigate, handle pagination, and extract links."""
    if url in visited_urls or current_depth > MAX_DEPTH:
        return
    
    if urlparse(url).netloc != base_domain:
        return

    print(f"[Depth {current_depth}] Navigating to: {url}")
    visited_urls.add(url)

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await human_delay(2, 4) 

        # Only run pagination logic on the main index page (Depth 0)
        if current_depth == 0:
            if PAGINATION_MODE == 'scroll':
                await handle_infinite_scroll(page)
            elif PAGINATION_MODE == 'button':
                await handle_button_pagination(page)

        # Extract page HTML and title AFTER pagination has fully loaded the DOM
        html_content = await page.content()
        title = await page.title()
        
        # Parse and save the text
        extract_and_save_text(html_content, url, current_depth, title)

        # If we are allowed to go deeper, harvest links from the current page state
        if current_depth < MAX_DEPTH:
            print(f"[Depth {current_depth}] Extracting sub-links...")
            links = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a'))
                            .map(anchor => anchor.getAttribute('href'))
                            .filter(href => href !== null);
            }""")

            discovered_urls = set()
            for link in links:
                # Clean up the link and make sure it's an absolute URL
                full_url = urljoin(url, link).split('#')[0] 
                if full_url not in visited_urls and urlparse(full_url).netloc == base_domain:
                    discovered_urls.add(full_url)

            # Sequentially process discovered links to avoid IP rate-limiting
            for next_url in discovered_urls:
                await scrape_page(page, next_url, current_depth + 1, base_domain)

    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

async def main():
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        
    print(f"Starting Scraper targeting: {TARGET_URL}")
    base_domain = urlparse(TARGET_URL).netloc

    async with async_playwright() as p:
        # Launch stealth browser
        browser = await p.chromium.launch(headless=True)
        
        # Configure context to mimic a legitimate desktop user
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            device_scale_factor=1,
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1"
            }
        )

        page = await context.new_page()

        # Begin recursive crawl
        await scrape_page(page, TARGET_URL, 0, base_domain)

        await context.close()
        await browser.close()
        print(f"\n✅ Scraping complete. All data saved to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    asyncio.run(main())