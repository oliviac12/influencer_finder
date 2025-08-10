#!/usr/bin/env python3
"""
Rebuild creator_post_lookup.csv from cached shoppable data
"""
import json
import pandas as pd
import os

def rebuild_post_lookup(dataset_name="radar_5k_quitmyjob"):
    """Rebuild creator_post_lookup.csv from dataset-specific caches"""
    
    creator_cache_file = f"cache/screening/{dataset_name}_cache/creator_cache.json"
    shoppable_cache_file = f"cache/screening/{dataset_name}_cache/shoppable_cache.json"
    
    if not os.path.exists(shoppable_cache_file):
        print("❌ No shoppable cache found!")
        return
    
    if not os.path.exists(creator_cache_file):
        print("❌ No creator cache found!")
        return
    
    # Load cached data
    with open(shoppable_cache_file, 'r') as f:
        shoppable_cache = json.load(f)
    
    with open(creator_cache_file, 'r') as f:
        creator_cache = json.load(f)
    
    print(f"📊 Found {len(shoppable_cache)} cached shoppable posts")
    print(f"📊 Found {len(creator_cache)} cached creators")
    
    # Rebuild detailed post lookup data
    post_data = []
    
    for username, creator_data in creator_cache.items():
        if creator_data.get('success') and 'posts' in creator_data:
            for post in creator_data['posts']:
                url = post.get('tiktok_url', '')
                if url in shoppable_cache:  # Only include posts we checked for shoppable content
                    post_row = {
                        'url': url,
                        'creator_username': username,
                        'is_shoppable': shoppable_cache[url],
                        'post_id': post.get('id', ''),
                        'description': post.get('description', ''),
                        'create_time': post.get('create_time', 0),
                        'formatted_date': post.get('formatted_date', ''),
                        'duration': post.get('duration', 0),
                        'is_photo_post': post.get('is_photo_post', False),
                        'content_type': post.get('content_type', 'video'),
                        'views': post.get('stats', {}).get('views', 0),
                        'likes': post.get('stats', {}).get('likes', 0),
                        'comments': post.get('stats', {}).get('comments', 0),
                        'shares': post.get('stats', {}).get('shares', 0)
                    }
                    post_data.append(post_row)
    
    if not post_data:
        print("❌ No post data found!")
        return
    
    # Save to CSV
    output_file = f'data/outputs/{dataset_name}_creator_post_lookup.csv'
    os.makedirs('data/outputs', exist_ok=True)
    df = pd.DataFrame(post_data)
    df.to_csv(output_file, index=False)
    
    print(f"✅ Rebuilt {output_file} with {len(post_data)} posts")
    
    # Show breakdown
    shoppable_count = sum(1 for row in post_data if row['is_shoppable'])
    not_shoppable_count = len(post_data) - shoppable_count
    print(f"   ✅ Shoppable posts: {shoppable_count}")
    print(f"   ❌ Not shoppable: {not_shoppable_count}")
    
    # Show creators breakdown
    unique_creators = len(set(row['creator_username'] for row in post_data))
    print(f"   👥 Unique creators: {unique_creators}")
    
    return output_file

if __name__ == "__main__":
    rebuild_post_lookup()