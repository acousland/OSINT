#!/usr/bin/env python3
"""
Test HTML processing capabilities for enhanced dossier generation
"""

from pathlib import Path
import re

def test_html_extraction():
    """Test HTML text extraction without dependencies"""
    
    print("🧪 Testing HTML Content Processing")
    print("=" * 50)
    
    # Check for HTML content
    html_dir = Path("downloads/www.abngroup.com.au/html_pages")
    
    if not html_dir.exists():
        print("❌ HTML directory not found")
        print("Please run the scraper first to generate test data")
        return False
    
    html_files = list(html_dir.glob("*.html"))
    print(f"📁 HTML files found: {len(html_files)}")
    
    if len(html_files) == 0:
        print("❌ No HTML files found")
        return False
    
    # Test HTML text extraction on a sample file
    sample_file = html_files[0]
    print(f"📄 Testing with: {sample_file.name}")
    
    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', ' ', content)
        text = ' '.join(text.split())  # Normalize whitespace
        
        print(f"📊 Original HTML size: {len(content)} characters")
        print(f"📊 Extracted text size: {len(text)} characters")
        print(f"📋 Sample text preview: {text[:200]}...")
        
        # Check metadata file
        metadata_file = html_dir / f"{sample_file.stem}_metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            print(f"🔗 URL: {metadata.get('url', 'N/A')}")
            print(f"📜 Title: {metadata.get('title', 'N/A')}")
        
        print("✅ HTML processing test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error processing HTML: {e}")
        return False

def test_content_variety():
    """Test variety of content available"""
    
    print("\n🔍 Content Variety Analysis")
    print("=" * 50)
    
    html_dir = Path("downloads/www.abngroup.com.au/html_pages")
    pdf_dir = Path("downloads/www.abngroup.com.au/pdfs")
    
    html_count = len(list(html_dir.glob("*.html"))) if html_dir.exists() else 0
    pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
    
    print(f"📄 PDF documents: {pdf_count}")
    print(f"🌐 HTML pages: {html_count}")
    print(f"📊 Total content sources: {pdf_count + html_count}")
    
    if html_count > 0:
        # Analyze HTML file types
        html_files = list(html_dir.glob("*.html"))
        
        # Categorize by filename patterns
        categories = {
            'about': [],
            'news': [],
            'careers': [],
            'companies': [],
            'contact': [],
            'other': []
        }
        
        for html_file in html_files:
            name = html_file.stem.lower()
            categorized = False
            
            for category in categories:
                if category in name:
                    categories[category].append(html_file.name)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(html_file.name)
        
        print("\n📋 HTML Content Categories:")
        for category, files in categories.items():
            if files:
                print(f"  {category.title()}: {len(files)} files")
                if len(files) <= 3:
                    for file in files:
                        print(f"    - {file}")
                else:
                    for file in files[:2]:
                        print(f"    - {file}")
                    print(f"    ... and {len(files) - 2} more")
    
    total_intelligence_value = html_count * 1 + pdf_count * 3  # PDFs typically have more content
    print(f"\n🎯 Estimated intelligence value: {total_intelligence_value} points")
    print("   (HTML=1pt each, PDF=3pts each - reflects typical content density)")
    
    return html_count > 0 or pdf_count > 0

if __name__ == "__main__":
    print("🚀 Enhanced OSINT Dossier Generator - HTML Processing Test")
    print("=" * 70)
    
    success1 = test_html_extraction()
    success2 = test_content_variety()
    
    print("\n🎉 Test Summary")
    print("=" * 30)
    
    if success1 and success2:
        print("✅ All tests passed!")
        print("🎯 Ready for enhanced dossier generation with HTML + PDF content")
        print("\n💡 The enhanced dossier generator will now process:")
        print("   - PDF documents for deep technical content")
        print("   - HTML pages for web content, news, and company information")
        print("   - Combined analysis for comprehensive intelligence reports")
    else:
        print("❌ Some tests failed")
        print("Please ensure content has been scraped before testing")
