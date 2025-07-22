import os
import asyncio
import aiohttp
import aiofiles
from fake_useragent import UserAgent
from urllib.parse import urlparse, urljoin, urlunparse
from lxml import html
import time
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import ssl
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HighSpeedWebMapper:
    def __init__(self, start_url, max_depth=1000, max_concurrent=50, request_delay=0.1):
        self.start_url = start_url
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        
        # URL management
        self.visited_urls = set()
        self.url_queue = deque([(start_url, 0)])  # (url, depth)
        self.found_urls = set()
        
        # Domain setup
        self.domain = urlparse(start_url).netloc
        self.base_download_dir = "downloads"
        self.download_dir = os.path.join(self.base_download_dir, self.domain)
        self.visited_urls_file = os.path.join(self.download_dir, 'visited_urls.txt')
        
        # Performance settings
        self.user_agent = UserAgent()
        self.session_timeout = aiohttp.ClientTimeout(total=10, connect=5)
        
        # Create download directory
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Clear previous results
        if os.path.exists(self.visited_urls_file):
            os.remove(self.visited_urls_file)
    
    def is_valid_url(self, url):
        """Check if URL is valid and should be processed"""
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not (parsed.netloc and parsed.scheme):
                return False
            
            # Must be internal to domain
            if parsed.netloc != self.domain:
                return False
            
            # Skip common non-page resources
            skip_extensions = {'.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.pdf', 
                             '.zip', '.doc', '.docx', '.xls', '.xlsx', '.ico', '.svg',
                             '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.avi'}
            
            path_lower = parsed.path.lower()
            if any(path_lower.endswith(ext) for ext in skip_extensions):
                return False
            
            # Skip common unwanted paths
            skip_paths = {'/wp-admin', '/admin', '/login', '/logout', '/search', 
                         '/feed', '/feeds', '/rss', '/atom', '/trackback'}
            
            if any(skip_path in path_lower for skip_path in skip_paths):
                return False
            
            return True
            
        except Exception:
            return False
    
    def normalize_url(self, url):
        """Normalize URL to avoid duplicates"""
        try:
            parsed = urlparse(url)
            # Remove fragment and normalize
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip('/') if parsed.path != '/' else '/',
                parsed.params,
                parsed.query,
                ''  # Remove fragment
            ))
            return normalized
        except Exception:
            return url
    
    async def fetch_url(self, session, url, depth):
        """Fetch a single URL and extract links"""
        if url in self.visited_urls or depth > self.max_depth:
            return []
        
        self.visited_urls.add(url)
        new_urls = []
        
        try:
            # Add random delay to avoid overwhelming server
            if self.request_delay > 0:
                await asyncio.sleep(self.request_delay)
            
            headers = {
                'User-Agent': self.user_agent.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200 and 'text/html' in response.headers.get('content-type', ''):
                    content = await response.text()
                    
                    # Parse HTML and extract links
                    try:
                        tree = html.fromstring(content)
                        
                        # Get all href attributes
                        hrefs = tree.xpath('//a/@href')
                        
                        for href in hrefs:
                            if href:
                                # Convert relative URLs to absolute
                                absolute_url = urljoin(url, href)
                                normalized_url = self.normalize_url(absolute_url)
                                
                                if (self.is_valid_url(normalized_url) and 
                                    normalized_url not in self.visited_urls and
                                    normalized_url not in self.found_urls):
                                    
                                    new_urls.append(normalized_url)
                                    self.found_urls.add(normalized_url)
                    
                    except Exception as e:
                        logger.debug(f"Failed to parse {url}: {e}")
                
                logger.info(f"✓ {url} (depth: {depth}, found: {len(new_urls)} new URLs)")
                
        except asyncio.TimeoutError:
            logger.warning(f"✗ Timeout: {url}")
        except Exception as e:
            logger.debug(f"✗ Error fetching {url}: {e}")
        
        return new_urls
    
    async def save_urls_batch(self, urls):
        """Save URLs to file in batches for better performance"""
        try:
            async with aiofiles.open(self.visited_urls_file, 'a') as f:
                for url in urls:
                    await f.write(f"{url}\n")
        except Exception as e:
            logger.error(f"Error saving URLs: {e}")
    
    async def map_website(self):
        """Main mapping function with high-speed concurrent processing"""
        start_time = time.time()
        
        # SSL context for better performance
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connection pooling for better performance
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent * 2,
            limit_per_host=self.max_concurrent,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl_context
        )
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.session_timeout
        ) as session:
            
            processed_count = 0
            save_batch = []
            
            while self.url_queue:
                # Create batch of concurrent requests
                current_batch = []
                batch_size = min(self.max_concurrent, len(self.url_queue))
                
                for _ in range(batch_size):
                    if self.url_queue:
                        url, depth = self.url_queue.popleft()
                        if url not in self.visited_urls:
                            current_batch.append((url, depth))
                
                if not current_batch:
                    break
                
                # Process batch concurrently
                tasks = [
                    self.fetch_url(session, url, depth) 
                    for url, depth in current_batch
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Add new URLs to queue and prepare for saving
                for i, result in enumerate(results):
                    if isinstance(result, list):
                        url, depth = current_batch[i]
                        save_batch.append(url)
                        
                        # Add new URLs to queue
                        for new_url in result:
                            if depth + 1 <= self.max_depth:
                                self.url_queue.append((new_url, depth + 1))
                
                processed_count += len(current_batch)
                
                # Save URLs in batches for better I/O performance
                if len(save_batch) >= 100:
                    await self.save_urls_batch(save_batch)
                    save_batch = []
                
                # Progress reporting
                if processed_count % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    logger.info(f"Progress: {processed_count} URLs processed, "
                              f"{len(self.url_queue)} in queue, "
                              f"{rate:.1f} URLs/sec")
            
            # Save remaining URLs
            if save_batch:
                await self.save_urls_batch(save_batch)
        
        # Final statistics
        end_time = time.time()
        total_time = end_time - start_time
        total_urls = len(self.visited_urls)
        
        logger.info(f"\n🎉 Mapping completed!")
        logger.info(f"📊 Total URLs found: {total_urls}")
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        logger.info(f"🚀 Average speed: {total_urls/total_time:.1f} URLs/second")
        logger.info(f"💾 Results saved to: {self.visited_urls_file}")
        
        return {
            'total_urls': total_urls,
            'total_time': total_time,
            'urls_per_second': total_urls/total_time if total_time > 0 else 0,
            'output_file': self.visited_urls_file
        }

# Legacy compatibility function
def map(start_url, max_depth=1000, max_concurrent=50, request_delay=0.1):
    """
    High-speed website mapping function
    
    Args:
        start_url: Starting URL to map
        max_depth: Maximum crawling depth
        max_concurrent: Maximum concurrent requests (50-100 recommended)
        request_delay: Delay between requests in seconds (0.1 recommended)
    """
    mapper = HighSpeedWebMapper(
        start_url=start_url,
        max_depth=max_depth,
        max_concurrent=max_concurrent,
        request_delay=request_delay
    )
    
    # Run the async function
    return asyncio.run(mapper.map_website())

# Even faster mapping with aggressive settings
def turbo_map(start_url, max_depth=1000):
    """
    Ultra-fast mapping with aggressive concurrent settings
    Use with caution - may overwhelm smaller servers
    """
    return map(
        start_url=start_url,
        max_depth=max_depth,
        max_concurrent=100,  # Very aggressive
        request_delay=0.05   # Minimal delay
    )

# Respectful fast mapping
def fast_map(start_url, max_depth=1000):
    """
    Fast but respectful mapping settings
    Good balance of speed and server-friendliness
    """
    return map(
        start_url=start_url,
        max_depth=max_depth,
        max_concurrent=30,   # Moderate concurrency
        request_delay=0.1    # Reasonable delay
    )

if __name__ == "__main__":
    # Example usage
    result = fast_map("https://example.com", max_depth=5)
    print(f"Mapped {result['total_urls']} URLs in {result['total_time']:.2f} seconds")