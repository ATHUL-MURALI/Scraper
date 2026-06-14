import os
from firecrawl import Firecrawl
from dotenv import load_dotenv
load_dotenv()

def main():
    # 1. Set your API key and target URL here
    API_KEY = os.getenv("fc-API-KEY")  # Replace with your actual Firecrawl API key
    TARGET_URL = "https://www.fca.org.uk/markets/sftr" # Replace with the URL you want to scrape
    # TARGET_URL = "https://www.amazon.in/gp/bestsellers" # Replace with the URL you want to scrape
    OUTPUT_FILE = "scraped_data1.md"

    print(f"Initializing Firecrawl app...")
    try:
        app = Firecrawl(api_key=API_KEY)

        print(f"Scraping {TARGET_URL}...")
        # We request only 'markdown' to keep it lightweight and fast (best for free credits)
        result = app.scrape(TARGET_URL, formats=['markdown'])

        # Extract the markdown content
        markdown_content = ""
        if isinstance(result, dict):
            markdown_content = result.get('markdown', '')
        else:
            # Fallback for different SDK object responses
            markdown_content = getattr(result, 'markdown', '')

        if not markdown_content:
            print("Warning: No markdown content retrieved.")
            return

        # Save the content to a Markdown file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write(markdown_content)

        print(f"Success! Data saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred during scraping: {e}")

if __name__ == "__main__":
    main()