import os
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import hashlib
from collections import deque

def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)

def get_page_content(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    return driver.page_source

def extract_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def get_links(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    return [urljoin(base_url, link.get('href')) for link in soup.find_all('a', href=True)]

def is_valid_url(url, base_domain):
    parsed_url = urlparse(url)
    return parsed_url.netloc == base_domain and parsed_url.scheme in ['http', 'https']

def clean_text(text):
    # Replace any sequence of more than 3 newlines with 3 newlines
    cleaned_text = re.sub(r'\n{4,}', '\n\n\n', text)
    return cleaned_text

def is_valid_page(url):
    # Check if the URL ends with common image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']
    return not any(url.lower().endswith(ext) for ext in image_extensions)

def crawl(start_url, output_folder="crawled_pages", max_depth=3):
    driver = setup_driver()
    base_domain = urlparse(start_url).netloc
    visited = set()
    to_visit = deque([(start_url, 0)])  # (url, depth)
    content_hashes = set()

    while to_visit:
        current_url, depth = to_visit.popleft()
        if current_url in visited or depth > max_depth:
            continue

        print(f"Crawling: {current_url} (Depth: {depth})")
        visited.add(current_url)

        try:
            if not is_valid_page(current_url):
                print(f"Skipping non-webpage: {current_url}")
                continue

            html_content = get_page_content(driver, current_url)
            text_content = extract_text(html_content)
            cleaned_text = clean_text(text_content)

            # check if we've seen this content before
            content_hash = hashlib.md5(cleaned_text.encode()).hexdigest()
            if content_hash in content_hashes:
                print(f"Skipping duplicate content: {current_url}")
                continue
            content_hashes.add(content_hash)

            # Save content to file
            cleaned_url_for_filename = urlparse(current_url).path.strip('/').replace('/', '_')
            # Don't save privacy/legal pages
            if any(x in cleaned_url_for_filename for x in ['cookie', 'privacy', 'legal']):
                print(f"Skipping privacy/legal page: {current_url}")
                continue
            # Special case for homepage to avoid system filenaming (i.e. file starts with period)
            filename = os.path.join(output_folder, cleaned_url_for_filename + '.txt' if cleaned_url_for_filename != "" else "homepage.txt")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)

            # Add new links to visit if we haven't reached max depth
            if depth < max_depth:
                new_links = get_links(html_content, current_url)
                for link in new_links:
                    if is_valid_url(link, base_domain) and link not in visited:
                        to_visit.append((link, depth + 1))

        except Exception as e:
            print(f"Error crawling {current_url}: {e}")

    driver.quit()

if __name__ == "__main__":
    start_url = "https://example.com" 
    output_folder = "crawled_pages"
    max_depth = 1
    crawl(start_url, max_depth=max_depth)