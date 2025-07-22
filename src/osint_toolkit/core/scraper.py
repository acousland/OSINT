import os
import asyncio
import aiohttp
import aiofiles
import requests
from urllib.parse import urlparse, urljoin
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
import time
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HighSpeedScraper:
    def __init__(self, start_url, max_concurrent=20):
        self.start_url = start_url
        self.max_concurrent = max_concurrent
        
        # Setup directories
        self.domain = urlparse(start_url).netloc
        self.base_download_dir = "downloads"
        self.download_dir = os.path.join(self.base_download_dir, self.domain)
        self.visited_urls_file = os.path.join(self.download_dir, 'visited_urls.txt')
        self.pdf_dir = os.path.join(self.download_dir, 'pdfs')
        self.html_dir = os.path.join(self.download_dir, 'html_pages')
        
        # Create directories
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.html_dir, exist_ok=True)
        
        # Performance tracking
        self.downloaded_count = 0
        self.failed_count = 0
        self.start_time = None
        
        self.user_agent = UserAgent()
    
    def clean_filename(self, url):
        """Create a safe filename from URL"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            filename = "index"
        else:
            # Replace path separators and clean up
            filename = path.replace('/', '_').replace('\\', '_')
            # Remove or replace invalid characters
            invalid_chars = '<>:"|?*'
            for char in invalid_chars:
                filename = filename.replace(char, '_')
        
        # Limit filename length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    async def download_pdf_direct(self, session, url):
        """Download a direct PDF file"""
        try:
            headers = {'User-Agent': self.user_agent.random}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    filename = self.clean_filename(url)
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    
                    filepath = os.path.join(self.pdf_dir, filename)
                    
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    logger.info(f"✅ Downloaded PDF: {url}")
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to download PDF {url}: {e}")
        return False
    
    async def save_html_page(self, session, url):
        """Save HTML page content"""
        try:
            headers = {
                'User-Agent': self.user_agent.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200 and 'text/html' in response.headers.get('content-type', ''):
                    content = await response.text()
                    
                    filename = self.clean_filename(url)
                    filepath = os.path.join(self.html_dir, f"{filename}.html")
                    
                    async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                        await f.write(content)
                    
                    # Also save metadata
                    metadata = {
                        'url': url,
                        'filename': filename,
                        'timestamp': time.time(),
                        'status_code': response.status,
                        'content_type': response.headers.get('content-type', ''),
                        'title': self.extract_title_from_content(content)
                    }
                    
                    metadata_path = os.path.join(self.html_dir, f"{filename}_metadata.json")
                    async with aiofiles.open(metadata_path, 'w') as f:
                        await f.write(json.dumps(metadata, indent=2))
                    
                    logger.info(f"✅ Saved HTML: {url}")
                    return True
        except Exception as e:
            logger.error(f"❌ Failed to save HTML {url}: {e}")
        return False
    
    def extract_title_from_content(self, content):
        """Extract page title from HTML content"""
        try:
            from lxml import html
            tree = html.fromstring(content)
            title_elements = tree.xpath('//title/text()')
            if title_elements:
                return title_elements[0].strip()
        except:
            pass
        return "Unknown Title"
    
    async def process_url(self, session, url):
        """Process a single URL - download PDF or save HTML"""
        try:
            # Check if it's a direct PDF
            if url.lower().endswith('.pdf') or '.pdf' in url.lower():
                success = await self.download_pdf_direct(session, url)
            else:
                success = await self.save_html_page(session, url)
            
            if success:
                self.downloaded_count += 1
            else:
                self.failed_count += 1
                
            # Progress reporting
            total_processed = self.downloaded_count + self.failed_count
            if total_processed % 10 == 0:
                elapsed = time.time() - self.start_time
                rate = total_processed / elapsed if elapsed > 0 else 0
                logger.info(f"Progress: {total_processed} processed, "
                          f"{self.downloaded_count} successful, "
                          f"{rate:.1f} files/sec")
                
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            self.failed_count += 1
    
    async def scrape_all_urls(self):
        """Main scraping function"""
        # Read URLs from the mapping results
        if not os.path.exists(self.visited_urls_file):
            logger.error(f"No mapping results found at {self.visited_urls_file}")
            logger.info("Please run website mapping first!")
            return None
        
        with open(self.visited_urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        logger.info(f"🚀 Starting high-speed scraping of {len(urls)} URLs")
        self.start_time = time.time()
        
        # Connection settings for better performance
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            limit_per_host=self.max_concurrent,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            
            # Process URLs in batches
            batch_size = self.max_concurrent
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]
                
                tasks = [self.process_url(session, url) for url in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
        
        # Final statistics
        end_time = time.time()
        total_time = end_time - self.start_time
        total_processed = self.downloaded_count + self.failed_count
        
        logger.info(f"\n🎉 Scraping completed!")
        logger.info(f"📊 Total URLs processed: {total_processed}")
        logger.info(f"✅ Successful downloads: {self.downloaded_count}")
        logger.info(f"❌ Failed downloads: {self.failed_count}")
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        logger.info(f"🚀 Average speed: {total_processed/total_time:.1f} files/second")
        logger.info(f"📁 HTML pages saved to: {self.html_dir}")
        logger.info(f"📄 PDF files saved to: {self.pdf_dir}")
        
        return {
            'total_processed': total_processed,
            'successful': self.downloaded_count,
            'failed': self.failed_count,
            'total_time': total_time,
            'files_per_second': total_processed/total_time if total_time > 0 else 0,
            'html_dir': self.html_dir,
            'pdf_dir': self.pdf_dir
        }

# Legacy compatibility functions
def download_pdf(url, user_agent):
    """Legacy function for direct PDF download"""
    headers = {'User-Agent': user_agent.random}
    response = requests.get(url, headers=headers, stream=True)
    
    domain = urlparse(url).netloc
    download_dir = os.path.join("downloads", domain)
    pdf_dir = os.path.join(download_dir, 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    filename = url.split('/')[-1].split('?')[0] or f"pdf_{len(os.listdir(pdf_dir)) + 1}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    
    with open(filepath, 'wb') as pdf:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                pdf.write(chunk)
    
    print(f"Downloaded: {filename}")

def download(url):
    """Legacy download function - now saves HTML instead of converting to PDF"""
    user_agent = UserAgent()
    
    if '.pdf' in url.split('?')[0]:
        download_pdf(url, user_agent)
    else:
        try:
            print(f"Saving {url} as HTML...")
            
            # Setup directories
            domain = urlparse(url).netloc
            download_dir = os.path.join("downloads", domain)
            html_dir = os.path.join(download_dir, 'html_pages')
            os.makedirs(html_dir, exist_ok=True)
            
            headers = {'User-Agent': user_agent.random}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                filename = urlparse(url).path.replace('/', '_') or 'index'
                # Clean filename
                invalid_chars = '<>:"|?*'
                for char in invalid_chars:
                    filename = filename.replace(char, '_')
                
                filepath = os.path.join(html_dir, f"{filename}.html")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                print(f"Saved HTML: {filename}.html")
            else:
                print(f"Failed to fetch {url}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"An error occurred while saving {url}: {e}")

def scrape(START_URL, max_concurrent=20):
    """
    High-speed scraping function that saves HTML pages and downloads PDFs
    
    Args:
        START_URL: The base URL that was mapped
        max_concurrent: Maximum concurrent downloads (default: 20)
    """
    scraper = HighSpeedScraper(START_URL, max_concurrent)
    return asyncio.run(scraper.scrape_all_urls())

# Fast scraping mode
def fast_scrape(START_URL):
    """Fast scraping with high concurrency"""
    return scrape(START_URL, max_concurrent=30)

# Turbo scraping mode  
def turbo_scrape(START_URL):
    """Maximum speed scraping (use carefully)"""
    return scrape(START_URL, max_concurrent=50)