import os
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin
from lxml import html
import requests

def scan_website(url, current_depth=0, max_depth=1000):
    if url in VISITED_URLS or current_depth > max_depth or is_internal_link(url) is False:
        return

    VISITED_URLS.add(url)
    with open(VISITED_URLS_FILE, 'a') as f:
        f.write(url + '\n')

    print(f"Scanning {url}...")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except (requests.RequestException, ValueError):
        return
    if response.content and response.content.strip():
        tree = html.fromstring(response.content)
        a_elements = tree.findall('.//a')
        hrefs = [a.get('href') for a in a_elements]
        for link in hrefs:
            if is_valid(link):
                scan_website(urljoin(url, link), current_depth + 1)
    else:
        print(f"No content returned from {url}")
# Check if a URL is valid
def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

# Check if a URL is internal to the website
def is_internal_link(link):
    return urlparse(link).netloc == DOMAIN

# Scan a website recursively
def map(START_URL, MAX_DEPTH=1000):
    global VISITED_URLS
    global VISITED_URLS_FILE
    global DOMAIN
    global DOWNLOAD_DIR
    global BASE_DOWNLOAD_DIR

    DOMAIN = urlparse(START_URL).netloc
    BASE_DOWNLOAD_DIR = "downloads"
    DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, DOMAIN)
    VISITED_URLS_FILE = os.path.join(DOWNLOAD_DIR, 'visited_urls.txt')
    user_agent = UserAgent()


    if os.path.exists(VISITED_URLS_FILE):
        os.remove(VISITED_URLS_FILE)
    
    VISITED_URLS = set()

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    scan_website(START_URL,0,MAX_DEPTH)

if __name__ == "__main__":
    map()