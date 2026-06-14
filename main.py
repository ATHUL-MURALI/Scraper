import requests
from bs4 import BeautifulSoup
import os
import time

def main():
    TARGET_URL = "https://www.amazon.in/gp/bestsellers" 
    OUTPUT_FILE = "scraped_data_bs4_rep.md"
    
    # Configure your test settings
    TOTAL_ATTEMPTS = 50   # How many times you want to run the loop
    DELAY_BETWEEN_REQUESTS = 0 # Delay in seconds to see how aggressive their rate-limiting is

    # Use headers to mimic a real web browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    # Initialize counters
    success_count = 0
    blocked_count = 0

    # Clear or initialize the markdown file with a header
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(f"# Rate Limit & Block Testing for {TARGET_URL}\n\n")
        file.write("| Attempt | Status Code | Result | Timestamp |\n")
        file.write("|---|---|---|---|\n")

    print(f"Starting test: Making {TOTAL_ATTEMPTS} requests to {TARGET_URL}...\n")

    for i in range(1, TOTAL_ATTEMPTS + 1):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Attempt {i}/{TOTAL_ATTEMPTS}...", end=" ", flush=True)

        try:
            # Fetch the webpage
            response = requests.get(TARGET_URL, headers=headers, timeout=15)
            status_code = response.status_code
            
            # Check for HTTP errors
            response.raise_for_status()

            # Parse the HTML to verify content actually exists
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.get_text(strip=True)

            if "api-services-support@amazon.com" in content or "Robot Check" in soup.title.text if soup.title else False:
                # Catching Amazon's soft-block (where status is 200 but page is a Captcha)
                print("BLOCKED (Captcha Page)")
                blocked_count += 1
                log_entry = f"| {i} | {status_code} | ❌ Blocked (Captcha/Robot Check Page) | {timestamp} |\n"
            elif not content:
                print("EMPTY RESPONSE")
                log_entry = f"| {i} | {status_code} | ⚠️ Empty Page Body | {timestamp} |\n"
            else:
                print("SUCCESS")
                success_count += 1
                log_entry = f"| {i} | {status_code} |  Success | {timestamp} |\n"

        except requests.exceptions.HTTPError as e:
            # Handles explicit HTTP errors like 403 Forbidden or 503 Service Unavailable
            status_code = e.response.status_code if e.response is not None else "Unknown"
            print(f"BLOCKED (HTTP {status_code})")
            blocked_count += 1
            log_entry = f"| {i} | {status_code} | ❌ Blocked ({e}) | {timestamp} |\n"

        except requests.exceptions.RequestException as e:
            # Handles connection drops, timeouts, DNS issues
            print("FAILED (Network Error)")
            log_entry = f"| {i} | Error | 💥 Connection Failed ({str(e)[:50]}...) | {timestamp} |\n"

        # Append the result of this iteration directly into the markdown file
        with open(OUTPUT_FILE, "a", encoding="utf-8") as file:
            file.write(log_entry)

        # Break early or add a delay before the next hit
        if i < TOTAL_ATTEMPTS:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Append final summary at the bottom of the file
    summary = (
        f"\n\n## Test Summary\n"
        f"* **Total Attempts:** {TOTAL_ATTEMPTS}\n"
        f"* **Successful Requests:** {success_count}\n"
        f"* **Blocked/Failed Requests:** {TOTAL_ATTEMPTS - success_count}\n"
    )
    with open(OUTPUT_FILE, "a", encoding="utf-8") as file:
        file.write(summary)

    print(f"\nTesting complete! Summary metrics appended to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()