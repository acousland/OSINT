import os
import pdfkit
import requests
from urllib.parse import urlparse
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor

def download_pdf(url, user_agent):
    headers = {'User-Agent': user_agent.random}
    response = requests.get(url, headers=headers, stream=True)
    
    filename = url.split('/')[-1].split('?')[0] or f"pdf_{len(os.listdir(DOWNLOAD_DIR)) + 1}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    
    with open(filepath, 'wb') as pdf:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                pdf.write(chunk)


def download(url):
    if '.pdf' in url.split('?')[0]:
        download_pdf(url, user_agent)
    else:
        try:
            print(f"Printing {url} to PDF...")
            filename = urlparse(url).path.replace('/', '_') or 'index'
            filepath = os.path.join(PDF_DIR, f"{filename}.pdf")
            pdfkit.from_url(url, filepath)
            print(f"Finished printing {url} to PDF")
        except Exception as e:
            print(f"An error occurred while printing {url} to PDF: {e}")

   

def scrape(START_URL):
    global PDF_DIR
    global DOWNLOAD_DIR
    global user_agent

    user_agent = UserAgent()
    DOMAIN = urlparse(START_URL).netloc
    BASE_DOWNLOAD_DIR = "downloads"
    DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, DOMAIN)
    VISITED_URLS_FILE = os.path.join(DOWNLOAD_DIR, 'visited_urls.txt')
    PDF_DIR = os.path.join(DOWNLOAD_DIR, 'pdfs')
    
    os.makedirs(PDF_DIR, exist_ok=True)
    
    # Read the URLs from the file
    with open(VISITED_URLS_FILE, 'r') as f:
        urls = [line.strip() for line in f]

    # Download the PDFs in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(download, urls)