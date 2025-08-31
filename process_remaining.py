"""
Process the remaining creators that weren't completed in the main batch
"""
import csv
import time
from clients.creator_data_client import CreatorDataClient
from utils.content_database import ContentDatabase

# Initialize clients
import os
from dotenv import load_dotenv
load_dotenv()

tikapi_key = "V0XpslK6h17qiYoa1JQq0eM9MdTRhqeY"
brightdata_token = os.getenv('BRIGHTDATA_TOKEN', '36c74962-d03a-41c1-b261-7ea4109ec8bd')

client = CreatorDataClient(tikapi_key=tikapi_key, brightdata_token=brightdata_token)
content_db = ContentDatabase()

# Read remaining creators
with open('remaining_creators.csv', 'r') as f:
    reader = csv.DictReader(f)
    remaining_creators = [row['username'] for row in reader]

print(f"📦 Processing {len(remaining_creators)} remaining creators")
print("="*60)

qualified = []
processed = 0
errors = 0

for username in remaining_creators:
    processed += 1
    print(f"[{processed}/{len(remaining_creators)}] @{username}", end=" - ")
    
    try:
        # Fetch creator data
        creator_data = client.get_creator_analysis(username, post_count=15)
        
        if not creator_data or not creator_data.get('posts'):
            print("❌ Failed to fetch data")
            errors += 1
            continue
            
        # Check if they have shoppable content
        has_shop = any(post.get('is_shop', False) for post in creator_data.get('posts', []))
        
        avg_views = creator_data.get('avg_video_views', 0)
        
        if has_shop and avg_views > 0:
            print(f"✅ QUALIFIED - {avg_views:,} avg views")
            qualified.append({
                'username': username,
                'avg_views': avg_views,
                'follower_count': creator_data.get('follower_count', 0),
                'bio': creator_data.get('biography', ''),
                'email': creator_data.get('email', '')
            })
        else:
            print(f"❌ Not qualified (shop={has_shop}, views={avg_views})")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        errors += 1
        
    # Small delay to avoid rate limits
    time.sleep(0.5)

print("\n" + "="*60)
print(f"✅ Found {len(qualified)} more qualified creators!")
print(f"❌ Errors: {errors}")

# Append to existing CSV
if qualified:
    print("\n💾 Appending to creator_lookup.csv...")
    
    # Read existing data to check for duplicates
    existing = set()
    try:
        with open('creator_lookup.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add(row['username'])
    except:
        pass
    
    # Append new qualified creators
    file_exists = len(existing) > 0
    with open('creator_lookup.csv', 'a', newline='') as f:
        fieldnames = ['username', 'nickname', 'bio', 'follower_count', 'following_count', 
                     'video_count', 'verified', 'sec_uid']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        for creator in qualified:
            if creator['username'] not in existing:
                writer.writerow({
                    'username': creator['username'],
                    'nickname': '',
                    'bio': creator['bio'],
                    'follower_count': creator['follower_count'],
                    'following_count': 0,
                    'video_count': 0,
                    'verified': False,
                    'sec_uid': ''
                })
    
    print(f"✅ Added {len(qualified)} new qualified creators")
    print("\nNew qualified creators:")
    for creator in qualified:
        print(f"  @{creator['username']} - {creator['avg_views']:,} avg views")

print("\n✨ Processing complete!")