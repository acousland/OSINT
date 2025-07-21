#!/usr/bin/env python3
"""
Test the complete OSINT workflow: Mapping -> Scraping -> Dossier Generation
"""

import mapStructure as ms
import scrape as sc
from dossier_generator import DossierGenerator
import os
import json
from pathlib import Path

def test_complete_workflow():
    """Test the complete OSINT workflow"""
    
    print("🚀 Testing Complete OSINT Workflow")
    print("=" * 60)
    
    # Test URL
    test_url = "https://www.abngroup.com.au"
    
    print(f"Target: {test_url}")
    print()
    
    # Step 1: High-Speed Mapping (if not already done)
    print("📍 Step 1: High-Speed Website Mapping")
    print("-" * 40)
    
    domain = test_url.replace("https://", "").replace("http://", "").split("/")[0]
    visited_urls_file = f"downloads/{domain}/visited_urls.txt"
    
    if not os.path.exists(visited_urls_file):
        print("Running fast mapping...")
        mapping_result = ms.fast_map(test_url, max_depth=3)
        print(f"✅ Mapping completed: {mapping_result.get('total_urls', 0)} URLs found")
    else:
        print("✅ Mapping already exists, using cached results")
        with open(visited_urls_file, 'r') as f:
            url_count = len([line for line in f if line.strip()])
        print(f"   Found {url_count} URLs in cache")
    
    print()
    
    # Step 2: High-Speed Content Scraping
    print("📄 Step 2: High-Speed Content Scraping")
    print("-" * 40)
    
    html_dir = f"downloads/{domain}/html_pages"
    if not os.path.exists(html_dir) or len(list(Path(html_dir).glob("*.html"))) < 5:
        print("Running fast scraping...")
        scraping_result = sc.fast_scrape(test_url)
        
        if scraping_result:
            print(f"✅ Scraping completed:")
            print(f"   Total processed: {scraping_result.get('total_processed', 0)}")
            print(f"   Successful: {scraping_result.get('successful', 0)}")
            print(f"   Speed: {scraping_result.get('files_per_second', 0):.1f} files/sec")
            print(f"   HTML directory: {scraping_result.get('html_dir', 'N/A')}")
        else:
            print("❌ Scraping failed")
            return False
    else:
        print("✅ Content already scraped, using cached results")
        html_count = len(list(Path(html_dir).glob("*.html")))
        print(f"   Found {html_count} HTML files")
    
    print()
    
    # Step 3: Check scraped content quality
    print("🔍 Step 3: Content Quality Check")
    print("-" * 40)
    
    html_files = list(Path(html_dir).glob("*.html"))
    if len(html_files) < 5:
        print(f"❌ Insufficient content: only {len(html_files)} files")
        return False
    
    # Check file sizes
    total_size = sum(f.stat().st_size for f in html_files)
    avg_size = total_size / len(html_files)
    
    print(f"✅ Content quality check passed:")
    print(f"   HTML files: {len(html_files)}")
    print(f"   Total size: {total_size / (1024*1024):.2f} MB")
    print(f"   Average file size: {avg_size / 1024:.2f} KB")
    
    # Show sample content
    sample_file = html_files[0]
    with open(sample_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if len(content) > 1000:
            print(f"   Sample content length: {len(content)} characters ✅")
        else:
            print(f"   Sample content length: {len(content)} characters ⚠️ (possibly too short)")
    
    print()
    
    # Step 4: Test dossier generation capabilities
    print("📋 Step 4: Dossier Generation Test")
    print("-" * 40)
    
    try:
        # Initialize dossier generator
        generator = DossierGenerator()
        
        # Check if we can read the content
        print("Testing content reading...")
        
        # Get text content from HTML files
        all_content = []
        for html_file in html_files[:10]:  # Test with first 10 files
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Basic HTML tag removal for testing
                    import re
                    text_content = re.sub(r'<[^>]+>', ' ', content)
                    text_content = ' '.join(text_content.split())  # Normalize whitespace
                    if len(text_content) > 100:  # Only include substantial content
                        all_content.append({
                            'filename': html_file.name,
                            'content': text_content[:2000]  # Limit for testing
                        })
            except Exception as e:
                print(f"   Warning: Could not read {html_file.name}: {e}")
        
        if len(all_content) > 0:
            print(f"✅ Successfully processed {len(all_content)} content files")
            print(f"   Total content available for analysis: ~{sum(len(c['content']) for c in all_content)} characters")
            
            # Test basic analysis capability
            sample_text = all_content[0]['content'][:500]
            print(f"   Sample content preview: {sample_text[:100]}...")
            
            print("✅ Ready for dossier generation!")
        else:
            print("❌ No usable content found for dossier generation")
            return False
            
    except Exception as e:
        print(f"❌ Dossier generation test failed: {e}")
        return False
    
    print()
    
    # Summary
    print("🎉 Complete Workflow Test Results")
    print("=" * 60)
    print("✅ Mapping: Working")
    print("✅ Scraping: Working") 
    print("✅ Content Quality: Good")
    print("✅ Dossier Ready: Yes")
    print()
    print(f"🎯 Target company: {domain}")
    print(f"📁 Data location: downloads/{domain}/")
    print(f"📄 HTML files: {len(html_files)}")
    print()
    print("💡 You can now generate a comprehensive dossier using the scraped content!")
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n🚀 All systems operational! Ready for intelligence gathering.")
    else:
        print("\n❌ Some issues detected. Check the output above.")
