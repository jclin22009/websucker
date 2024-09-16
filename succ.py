import os
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import hashlib

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

def crawl(start_url, output_folder):
    driver = setup_driver()
    base_domain = urlparse(start_url).netloc
    visited = set()
    to_visit = [start_url]
    content_hashes = set()

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue

        print(f"Crawling: {current_url}")
        visited.add(current_url)

        try:
            html_content = get_page_content(driver, current_url)
            text_content = extract_text(html_content)

            # check if we've seen this content before. Shoutout claude
            content_hash = hashlib.md5(text_content.encode()).hexdigest()
            if content_hash in content_hashes:
                print(f"Skipping duplicate content: {current_url}")
                continue
            content_hashes.add(content_hash)

            # Save content to file
            filename = os.path.join(output_folder, urlparse(current_url).path.strip('/').replace('/', '_') + '.txt')
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text_content)

            # Add new links to visit
            new_links = get_links(html_content, current_url)
            to_visit.extend([link for link in new_links if is_valid_url(link, base_domain) and link not in visited])

        except Exception as e:
            print(f"Error crawling {current_url}: {e}")

    driver.quit()

if __name__ == "__main__":
    start_url = "https://example.com" 
    output_folder = "crawled_pages"
    crawl(start_url, output_folder)