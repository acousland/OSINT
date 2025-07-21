#!/usr/bin/env python3
"""
Test script for high-speed website mapping
"""

import mapStructure as ms
import time
import sys

def test_mapping_speed():
    """Test the high-speed mapping functionality"""
    
    print("🚀 Testing High-Speed Website Mapping")
    print("=" * 50)
    
    # Test URL (using a reliable test site)
    test_url = "https://httpbin.org"
    max_depth = 3
    
    print(f"Target: {test_url}")
    print(f"Max Depth: {max_depth}")
    print()
    
    # Test different speed modes
    modes = [
        ("Respectful", lambda: ms.map(test_url, max_depth, max_concurrent=10, request_delay=0.2)),
        ("Fast", lambda: ms.fast_map(test_url, max_depth)),
        ("Turbo", lambda: ms.turbo_map(test_url, max_depth))
    ]
    
    results = []
    
    for mode_name, mapping_func in modes:
        print(f"🧪 Testing {mode_name} mode...")
        try:
            start_time = time.time()
            result = mapping_func()
            end_time = time.time()
            
            if result:
                print(f"✅ {mode_name} completed successfully!")
                print(f"   URLs found: {result.get('total_urls', 0)}")
                print(f"   Time taken: {result.get('total_time', 0):.2f}s")
                print(f"   Speed: {result.get('urls_per_second', 0):.1f} URLs/sec")
                results.append((mode_name, result))
            else:
                print(f"❌ {mode_name} returned no results")
                
        except Exception as e:
            print(f"❌ {mode_name} failed: {e}")
        
        print("-" * 30)
    
    # Summary
    if results:
        print("\n📊 Performance Summary:")
        print("Mode\t\tURLs\tTime\tSpeed (URLs/sec)")
        print("-" * 45)
        for mode_name, result in results:
            urls = result.get('total_urls', 0)
            time_taken = result.get('total_time', 0)
            speed = result.get('urls_per_second', 0)
            print(f"{mode_name:<12}\t{urls}\t{time_taken:.2f}s\t{speed:.1f}")
        
        print("\n🎉 Speed test completed!")
        return True
    else:
        print("❌ No successful tests")
        return False

if __name__ == "__main__":
    success = test_mapping_speed()
    sys.exit(0 if success else 1)
