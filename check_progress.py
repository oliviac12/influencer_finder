#!/usr/bin/env python3
"""
Quick script to check backfill progress
"""
from utils.content_database import ContentDatabase
import json

db = ContentDatabase()
stats = db.get_stats()

print("📊 Content Database Progress:")
print(f"   Creators processed: {stats['creator_count']}")
print(f"   Total posts: {stats['total_posts']}")
print(f"   Last updated: {stats['last_updated']}")
print(f"   Average posts per creator: {stats['total_posts'] / stats['creator_count']:.1f}")

# Estimate progress
estimated_total = 970
progress_pct = (stats['creator_count'] / estimated_total) * 100
print(f"   Estimated progress: {progress_pct:.1f}% ({stats['creator_count']}/{estimated_total})")

print(f"\n📁 Database size: ", end="")
import os
try:
    size = os.path.getsize("cache/creators_content_database.json")
    print(f"{size/1024/1024:.1f} MB")
except:
    print("Unknown")