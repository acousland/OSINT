#!/usr/bin/env python3
"""
OSINT Toolkit - In-Memory Pipeline Demo
Quick demonstration of the streamlined in-memory workflow
"""

import asyncio
import time
from src.osint_toolkit.core.in_memory_mapper import InMemoryWebMapper
from src.osint_toolkit.core.in_memory_scraper import InMemoryScraper

async def demo_pipeline():
    """Demonstrate the in-memory pipeline"""
    
    print("🔍 OSINT Toolkit - In-Memory Pipeline Demo")
    print("=" * 50)
    
    # Test URL (using a simple, fast site for demo)
    test_url = "https://httpbin.org"
    
    print(f"📡 Target: {test_url}")
    print()
    
    # Phase 1: Mapping
    print("🗺️  Phase 1: Website Mapping")
    print("-" * 30)
    
    mapper = InMemoryWebMapper(max_concurrent=10, max_depth=2)
    
    def mapping_progress(msg):
        print(f"   {msg}")
    
    start_time = time.time()
    mapping_results = await mapper.map_website(test_url, mapping_progress)
    mapping_time = time.time() - start_time
    
    print(f"✅ Mapping complete in {mapping_time:.2f}s")
    print(f"   - Found {len(mapping_results['discovered_urls'])} URLs")
    print(f"   - Speed: {mapping_results['stats']['urls_per_second']:.1f} URLs/sec")
    print()
    
    # Phase 2: Scraping (limit to first 5 URLs for demo)
    print("📥 Phase 2: Content Scraping")
    print("-" * 30)
    
    scraper = InMemoryScraper(max_concurrent=5)
    urls_to_scrape = mapping_results['discovered_urls'][:5]  # Limit for demo
    
    def scraping_progress(msg):
        print(f"   {msg}")
    
    start_time = time.time()
    scraping_results = await scraper.scrape_content(urls_to_scrape, scraping_progress)
    scraping_time = time.time() - start_time
    
    print(f"✅ Scraping complete in {scraping_time:.2f}s")
    print(f"   - HTML pages: {scraping_results['stats']['html_pages']}")
    print(f"   - PDF files: {scraping_results['stats']['pdf_files']}")
    print(f"   - Content size: {scraping_results['stats']['content_size_mb']:.2f} MB")
    print()
    
    # Results summary
    print("📊 Pipeline Summary")
    print("-" * 30)
    print(f"Total time: {mapping_time + scraping_time:.2f}s")
    print(f"URLs processed: {len(urls_to_scrape)}")
    print(f"Content in memory: {scraping_results['stats']['content_size_mb']:.2f} MB")
    print()
    
    print("✅ Demo complete! In-memory pipeline working correctly.")
    print("🚀 Ready to use: ./run.sh streamlined")

if __name__ == "__main__":
    asyncio.run(demo_pipeline())
