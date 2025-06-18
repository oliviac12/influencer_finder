import sys
import json

try:
    from tikapi import TikAPI, ValidationException, ResponseException
    print("✅ TikAPI SDK is available")
except ImportError:
    print("❌ TikAPI SDK not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tikapi"])
    from tikapi import TikAPI, ValidationException, ResponseException
    print("✅ TikAPI SDK installed and imported")

# API configuration
API_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
test_username = "27travels"

print(f"Testing TikAPI - Getting recent posts for: {test_username}")
print("=" * 60)

api = TikAPI(API_KEY)

try:
    # Method 1: Use public.check to get profile info and secUid
    print("1. Getting profile info using public.check...")
    profile_response = api.public.check(username=test_username)
    
    if profile_response.status_code == 200:
        profile_data = profile_response.json()
        print(f"✅ Profile check successful!")
        
        # Extract user info
        user_info = profile_data.get('userInfo', {})
        user = user_info.get('user', {})
        stats = user_info.get('stats', {})
        
        sec_uid = user.get('secUid')
        unique_id = user.get('uniqueId')
        nickname = user.get('nickname')
        
        print(f"User: {unique_id} ({nickname})")
        print(f"SecUID: {sec_uid}")
        print(f"Followers: {stats.get('followerCount', 'N/A'):,}")
        print(f"Following: {stats.get('followingCount', 'N/A'):,}")
        print(f"Videos: {stats.get('videoCount', 'N/A'):,}")
        
        if sec_uid:
            # Now get posts using the secUid
            print(f"\n2. Getting recent posts...")
            posts_response = api.public.posts(secUid=sec_uid)
            
            if posts_response.status_code == 200:
                posts_data = posts_response.json()
                print(f"✅ Posts fetched successfully!")
                
                # Display post information
                if 'itemList' in posts_data and posts_data['itemList']:
                    posts = posts_data['itemList']
                    print(f"\n📊 Found {len(posts)} recent posts:")
                    
                    for i, post in enumerate(posts[:5]):  # Show first 5 posts
                        print(f"\n--- Post {i+1} ---")
                        print(f"ID: {post.get('id')}")
                        
                        desc = post.get('desc', 'No description')
                        print(f"Description: {desc[:100]}{'...' if len(desc) > 100 else ''}")
                        
                        create_time = post.get('createTime')
                        if create_time:
                            from datetime import datetime
                            dt = datetime.fromtimestamp(create_time)
                            print(f"Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # Video information
                        if 'video' in post:
                            video_info = post['video']
                            duration = video_info.get('duration', 0)
                            print(f"Duration: {duration} seconds")
                            
                            # Video URLs
                            if 'playAddr' in video_info:
                                video_url = video_info['playAddr']
                                print(f"Video URL: {video_url}")
                            
                            if 'downloadAddr' in video_info:
                                download_url = video_info['downloadAddr']
                                print(f"Download URL: {download_url}")
                        
                        # Engagement stats
                        if 'stats' in post:
                            stats = post['stats']
                            print(f"👀 Views: {stats.get('playCount', 0):,}")
                            print(f"❤️ Likes: {stats.get('diggCount', 0):,}")
                            print(f"💬 Comments: {stats.get('commentCount', 0):,}")
                            print(f"🔄 Shares: {stats.get('shareCount', 0):,}")
                    
                    print(f"\n🎯 SUCCESS! Retrieved {len(posts)} recent posts for {unique_id}")
                    
                else:
                    print("No posts found or unexpected response structure")
                    print(f"Available keys: {list(posts_data.keys())}")
                    
            else:
                print(f"❌ Posts request failed: {posts_response.status_code}")
                print(f"Error: {posts_response.text[:200]}...")
        else:
            print("❌ Could not extract secUid from profile")
            print(f"Available profile keys: {list(profile_data.keys())}")
    else:
        print(f"❌ Profile check failed: {profile_response.status_code}")
        print(f"Error: {profile_response.text[:200]}...")

except ValidationException as e:
    print(f"❌ Validation Error: {e}")
    if hasattr(e, 'field'):
        print(f"Field: {e.field}")

except ResponseException as e:
    print(f"❌ Response Error: {e}")
    print(f"Status Code: {e.response.status_code}")
    print(f"Response: {e.response.text[:200]}...")

except Exception as e:
    print(f"❌ General Error: {e}")

print(f"\n{'='*60}")
print("Test completed!")