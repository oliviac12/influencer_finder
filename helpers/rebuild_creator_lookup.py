#!/usr/bin/env python3
"""
Rebuild creator_lookup.csv from cached creator data
"""
import json
import pandas as pd
import os

def rebuild_creator_lookup():
    """Rebuild creator_lookup.csv from screening_cache/creator_cache.json"""
    
    cache_file = "../cache/screening/creator_cache.json"
    
    if not os.path.exists(cache_file):
        print("❌ No creator cache found!")
        return
    
    # Load cached creator data
    with open(cache_file, 'r') as f:
        creator_cache = json.load(f)
    
    # Extract creator profile data
    creator_data = []
    for username, data in creator_cache.items():
        if data.get('success') and 'profile' in data:
            profile = data['profile']
            creator_row = {
                'username': profile.get('username', username),
                'nickname': profile.get('nickname', ''),
                'bio': profile.get('signature', ''),
                'follower_count': profile.get('followers', 0),
                'following_count': profile.get('following', 0),
                'video_count': profile.get('videos', 0),
                'verified': profile.get('verified', False),
                'sec_uid': profile.get('sec_uid', '')
            }
            creator_data.append(creator_row)
    
    if not creator_data:
        print("❌ No valid creator data found in cache!")
        return
    
    # Save to CSV
    df = pd.DataFrame(creator_data)
    df.to_csv('creator_lookup.csv', index=False)
    
    print(f"✅ Rebuilt creator_lookup.csv with {len(creator_data)} creators:")
    for creator in creator_data:
        print(f"   • @{creator['username']} - {creator['follower_count']:,} followers")

if __name__ == "__main__":
    rebuild_creator_lookup()