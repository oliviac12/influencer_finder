#!/usr/bin/env python3
"""
Rebuild creator_post_lookup.csv from cached shoppable data
"""
import json
import pandas as pd
import os

def rebuild_post_lookup():
    """Rebuild creator_post_lookup.csv from screening_cache/shoppable_cache.json"""
    
    cache_file = "../cache/screening/shoppable_cache.json"
    
    if not os.path.exists(cache_file):
        print("❌ No shoppable cache found!")
        return
    
    # Load cached shoppable data
    with open(cache_file, 'r') as f:
        shoppable_cache = json.load(f)
    
    print(f"📊 Found {len(shoppable_cache)} cached posts")
    
    # Show sample of what we have
    print("\n🔍 Sample cached URLs:")
    for i, url in enumerate(list(shoppable_cache.keys())[:5]):
        is_shoppable = shoppable_cache[url]
        print(f"   {i+1}. {url} -> {is_shoppable}")
    
    print(f"\n📈 Shoppable breakdown:")
    shoppable_count = sum(1 for v in shoppable_cache.values() if v)
    not_shoppable_count = len(shoppable_cache) - shoppable_count
    print(f"   ✅ Shoppable: {shoppable_count}")
    print(f"   ❌ Not shoppable: {not_shoppable_count}")

if __name__ == "__main__":
    rebuild_post_lookup()