"""
In-Memory Website Mapper
High-speed website mapping that returns results in memory without file I/O
"""

import asyncio
import aiohttp
import time
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Any, Optional, Callable
from lxml import html
import logging

logger = logging.getLogger(__name__)

class InMemoryWebMapper:
    """High-speed website mapper that returns results in memory"""
    
    def __init__(self, max_concurrent: int = 30, max_depth: int = 3):
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self.discovered_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.url_depths: Dict[str, int] = {}
        
    async def map_website(self, base_url: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Map website structure and return results in memory
        
        Args:
            base_url: Starting URL to map
            progress_callback: Optional callback function for progress updates
            
        Returns:
            {
                'base_url': str,
                'discovered_urls': List[str],
                'failed_urls': List[str],
                'stats': {
                    'total_urls': int,
                    'successful': int,
                    'failed': int,
                    'time_taken': float,
                    'urls_per_second': float
                }
            }
        """
        start_time = time.time()
        
        # Reset state
        self.discovered_urls.clear()
        self.failed_urls.clear()
        self.url_depths.clear()
        
        # Validate base URL
        parsed_base = urlparse(base_url)
        if not parsed_base.netloc:
            raise ValueError(f"Invalid URL: {base_url}")
        
        base_domain = parsed_base.netloc
        
        # Configure aiohttp session
        connector = aiohttp.TCPConnector(
            limit=100, 
            limit_per_host=self.max_concurrent,
            ssl=False  # For faster processing, disable SSL verification
        )
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (OSINT-Toolkit/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        ) as session:
            
            # Start with base URL
            to_visit = [(base_url, 0)]  # (url, depth)
            self.discovered_urls.add(base_url)
            self.url_depths[base_url] = 0
            
            while to_visit:
                # Get current batch
                current_batch = to_visit[:self.max_concurrent]
                to_visit = to_visit[self.max_concurrent:]
                
                # Process batch concurrently
                tasks = [
                    self._process_url(session, url, depth, base_domain)
                    for url, depth in current_batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and add new URLs
                for result in batch_results:
                    if isinstance(result, list):  # Successful result with new URLs
                        for new_url, new_depth in result:
                            if (new_url not in self.discovered_urls and 
                                new_url not in self.failed_urls and
                                new_depth <= self.max_depth):
                                to_visit.append((new_url, new_depth))
                                self.discovered_urls.add(new_url)
                                self.url_depths[new_url] = new_depth
                
                # Update progress
                if progress_callback:
                    total_discovered = len(self.discovered_urls)
                    progress_callback(f"Discovered {total_discovered} URLs...")
                
                # Prevent infinite loops with reasonable limits
                if len(self.discovered_urls) > 1000:
                    logger.warning(f"URL limit reached (1000), stopping discovery")
                    break
        
        # Calculate statistics
        end_time = time.time()
        time_taken = end_time - start_time
        total_urls = len(self.discovered_urls)
        successful_urls = total_urls - len(self.failed_urls)
        urls_per_second = total_urls / time_taken if time_taken > 0 else 0
        
        return {
            'base_url': base_url,
            'discovered_urls': sorted(list(self.discovered_urls)),
            'failed_urls': sorted(list(self.failed_urls)),
            'stats': {
                'total_urls': total_urls,
                'successful': successful_urls,
                'failed': len(self.failed_urls),
                'time_taken': round(time_taken, 2),
                'urls_per_second': round(urls_per_second, 2)
            }
        }
    
    async def _process_url(self, session: aiohttp.ClientSession, url: str, depth: int, base_domain: str) -> List[tuple]:
        """Process a single URL and extract links"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    self.failed_urls.add(url)
                    return []
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    return []  # Not an HTML page
                
                content = await response.text()
                return self._extract_links(content, url, depth, base_domain)
                
        except Exception as e:
            logger.debug(f"Failed to process {url}: {e}")
            self.failed_urls.add(url)
            return []
    
    def _extract_links(self, content: str, base_url: str, current_depth: int, base_domain: str) -> List[tuple]:
        """Extract valid links from HTML content"""
        try:
            tree = html.fromstring(content)
            links = []
            
            # Extract all href attributes
            for element in tree.xpath('//a[@href]'):
                href = element.get('href')
                if not href:
                    continue
                
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                
                # Validate URL
                if self._is_valid_url(absolute_url, base_domain):
                    links.append((absolute_url, current_depth + 1))
            
            return links
            
        except Exception as e:
            logger.debug(f"Failed to extract links from {base_url}: {e}")
            return []
    
    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and should be processed"""
        try:
            parsed = urlparse(url)
            
            # Must be same domain
            if parsed.netloc != base_domain:
                return False
            
            # Skip fragments and certain file types
            if parsed.fragment:
                return False
            
            # Skip common non-content URLs
            skip_patterns = [
                'mailto:', 'tel:', 'javascript:', '#',
                '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg',
                '.ico', '.woff', '.ttf', '.eot'
            ]
            
            url_lower = url.lower()
            if any(pattern in url_lower for pattern in skip_patterns):
                return False
            
            return True
            
        except Exception:
            return False
