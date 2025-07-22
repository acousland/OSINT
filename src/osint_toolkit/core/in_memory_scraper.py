"""
In-Memory Website Scraper
High-speed content scraping that returns results in memory without file I/O
"""

import asyncio
import aiohttp
import time
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Any, Optional, Callable
from lxml import html
import logging

logger = logging.getLogger(__name__)

class InMemoryScraper:
    """High-speed scraper that returns content in memory"""
    
    def __init__(self, max_concurrent: int = 20):
        self.max_concurrent = max_concurrent
        
    async def scrape_content(self, urls: List[str], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Scrape content from URLs and return in memory
        
        Args:
            urls: List of URLs to scrape
            progress_callback: Optional callback for progress updates
            
        Returns:
            {
                'html_content': {url: {'content': str, 'title': str, 'text': str, 'metadata': dict}, ...},
                'pdf_content': {url: {'content': bytes, 'size': int}, ...},
                'failed_urls': List[str],
                'stats': {
                    'total_urls': int,
                    'html_pages': int,
                    'pdf_files': int,
                    'failed': int,
                    'time_taken': float,
                    'content_size_mb': float
                }
            }
        """
        start_time = time.time()
        
        html_content = {}
        pdf_content = {}
        failed_urls = []
        total_size = 0
        
        # Configure aiohttp session
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=self.max_concurrent,
            ssl=False
        )
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (OSINT-Toolkit/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,*/*;q=0.8'
            }
        ) as session:
            
            # Process URLs in batches
            for i in range(0, len(urls), self.max_concurrent):
                batch = urls[i:i + self.max_concurrent]
                
                # Create tasks for current batch
                tasks = [
                    self._scrape_single_url(session, url)
                    for url in batch
                ]
                
                # Process batch
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for url, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        failed_urls.append(url)
                        continue
                    
                    if result is None:
                        failed_urls.append(url)
                        continue
                    
                    content_type, content_data, size = result
                    total_size += size
                    
                    if content_type == 'html':
                        html_content[url] = content_data
                    elif content_type == 'pdf':
                        pdf_content[url] = content_data
                
                # Update progress
                if progress_callback:
                    processed = i + len(batch)
                    progress_callback(f"Scraped {processed}/{len(urls)} URLs...")
        
        # Calculate statistics
        end_time = time.time()
        time_taken = end_time - start_time
        content_size_mb = total_size / (1024 * 1024)
        
        return {
            'html_content': html_content,
            'pdf_content': pdf_content,
            'failed_urls': failed_urls,
            'stats': {
                'total_urls': len(urls),
                'html_pages': len(html_content),
                'pdf_files': len(pdf_content),
                'failed': len(failed_urls),
                'time_taken': round(time_taken, 2),
                'content_size_mb': round(content_size_mb, 2)
            }
        }
    
    async def _scrape_single_url(self, session: aiohttp.ClientSession, url: str) -> Optional[tuple]:
        """Scrape content from a single URL"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                content_type = response.headers.get('content-type', '').lower()
                
                # Handle PDF files
                if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
                    content = await response.read()
                    return ('pdf', {
                        'content': content,
                        'size': len(content),
                        'url': url
                    }, len(content))
                
                # Handle HTML pages
                elif 'text/html' in content_type:
                    content = await response.text()
                    parsed_content = self._parse_html_content(content, url)
                    content_size = len(content.encode('utf-8'))
                    return ('html', parsed_content, content_size)
                
                return None
                
        except Exception as e:
            logger.debug(f"Failed to scrape {url}: {e}")
            return None
    
    def _parse_html_content(self, content: str, url: str) -> Dict[str, Any]:
        """Parse HTML content and extract useful information"""
        try:
            tree = html.fromstring(content)
            
            # Extract title
            title_elements = tree.xpath('//title/text()')
            title = title_elements[0].strip() if title_elements else "No Title"
            
            # Extract text content (remove scripts, styles)
            # Remove script and style elements
            for element in tree.xpath('//script | //style'):
                element.getparent().remove(element)
            
            # Get text content
            text_content = tree.text_content()
            clean_text = ' '.join(text_content.split())  # Clean whitespace
            
            # Extract metadata
            meta_description = ""
            meta_keywords = ""
            
            for meta in tree.xpath('//meta'):
                name = meta.get('name', '').lower()
                content_attr = meta.get('content', '')
                
                if name == 'description':
                    meta_description = content_attr
                elif name == 'keywords':
                    meta_keywords = content_attr
            
            return {
                'content': content,
                'title': title,
                'text': clean_text,
                'metadata': {
                    'url': url,
                    'title': title,
                    'description': meta_description,
                    'keywords': meta_keywords,
                    'word_count': len(clean_text.split()),
                    'char_count': len(clean_text)
                }
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse HTML from {url}: {e}")
            return {
                'content': content,
                'title': 'Parse Error',
                'text': content[:1000],  # First 1000 chars as fallback
                'metadata': {
                    'url': url,
                    'title': 'Parse Error',
                    'description': '',
                    'keywords': '',
                    'word_count': 0,
                    'char_count': len(content)
                }
            }
