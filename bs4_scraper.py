import requests
from bs4 import BeautifulSoup
import os

def main():
    # Set your target URL here
    # TARGET_URL = "https://www.fca.org.uk/markets/sftr" 
    TARGET_URL = "https://www.amazon.in/gp/bestsellers" 
    OUTPUT_FILE = "scraped_data_bs4.md"

    print(f"Initializing scraping for {TARGET_URL}...")

    # Crucial: Use headers to mimic a real web browser to avoid immediate 403 errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    try:
        # 1. Fetch the webpage
        print("Fetching webpage...")
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        
        # This will raise an exception for HTTP errors (like 403 Forbidden or 404 Not Found)
        response.raise_for_status()

        # 2. Parse the HTML using BeautifulSoup
        print("Parsing HTML...")
        soup = BeautifulSoup(response.content, 'html.parser')

        # 3. Extract the text 
        # We use separator='\n\n' to give it a readable paragraph spacing
        content = soup.get_text(separator='\n\n', strip=True)

        if not content:
            print("Warning: No content could be extracted from the HTML.")
            return

        # 4. Save the successful content to the Markdown file
        print(f"Saving data to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write(f"# Scraped Data from {TARGET_URL}\n\n")
            file.write(content)

        print(f"Success! Data successfully saved to {OUTPUT_FILE}")

    except requests.exceptions.RequestException as e:
        # 5. Handle any blocking, timeouts, or network errors and save to the .md file
        error_msg = (
            f"# Error Scraping {TARGET_URL}\n\n"
            f"**An error occurred:**\n```text\n{str(e)}\n```\n\n"
            f"*Note: If this is a 403 or 503 error, the website's anti-bot protection blocked the request.*"
        )
        
        print(f"An error occurred. Saving error details to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write(error_msg)

if __name__ == "__main__":
    main()