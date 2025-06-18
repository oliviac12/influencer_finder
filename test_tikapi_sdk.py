import sys
import json

# First, let's check if tikapi is installed, if not, install it
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

print(f"Testing TikAPI SDK with creator: {test_username}")
print("=" * 60)

api = TikAPI(API_KEY)

# First, we need to get the user's secUid
# Let's try to search for the user first
print("1. Searching for user to get secUid...")
try:
    # Use the search functionality to find the user
    search_response = api.public.search(
        query=test_username,
        category="users"
    )
    
    search_data = search_response.json()
    print(f"✅ Search successful! Status: {search_response.status_code}")
    
    # Debug: print the actual response structure
    print(f"Search response keys: {list(search_data.keys())}")
    print(f"Search response (first 500 chars): {json.dumps(search_data, indent=2)[:500]}...")
    
    # Try different possible user list keys
    user_lists = ['user_list', 'users', 'userList', 'data', 'results']
    user = None
    
    for key in user_lists:
        if search_data.get(key) and len(search_data[key]) > 0:
            user = search_data[key][0]
            print(f"Found user data in key: {key}")
            break
    
    if user:
        print(f"User fields: {list(user.keys())}")
        
        # The actual user info is nested under 'user_info'
        if 'user_info' in user:
            user_info = user['user_info']
            print(f"User info fields: {list(user_info.keys())}")
            
            # Try different possible field names for secUid
            sec_uid_keys = ['sec_uid', 'secUid', 'secuid', 'sec_id']
            unique_id_keys = ['unique_id', 'uniqueId', 'username', 'user_name']
            
            sec_uid = None
            unique_id = None
            
            for key in sec_uid_keys:
                if user_info.get(key):
                    sec_uid = user_info.get(key)
                    break
                    
            for key in unique_id_keys:
                if user_info.get(key):
                    unique_id = user_info.get(key)
                    break
            
            print(f"Found user: {unique_id} with secUid: {sec_uid}")
        else:
            print("No user_info found in user object")
        
        # Now get posts using secUid
        print(f"\n2. Getting recent posts for {unique_id}...")
        posts_response = api.public.posts(secUid=sec_uid)
        
        posts_data = posts_response.json()
        print(f"✅ Posts fetched successfully!")
        
        # Display post information
        if 'itemList' in posts_data:
            posts = posts_data['itemList']
            print(f"\n📊 Found {len(posts)} recent posts:")
            
            for i, post in enumerate(posts[:3]):  # Show first 3 posts
                print(f"\n--- Post {i+1} ---")
                print(f"ID: {post.get('id')}")
                print(f"Description: {post.get('desc', 'No description')[:150]}...")
                print(f"Create Time: {post.get('createTime')}")
                
                # Video URL information
                if 'video' in post:
                    video_info = post['video']
                    print(f"Video Duration: {video_info.get('duration')} seconds")
                    if 'playAddr' in video_info:
                        print(f"Video URL: {video_info['playAddr'][:100]}...")
                
                # Stats
                if 'stats' in post:
                    stats = post['stats']
                    print(f"Views: {stats.get('playCount', 'N/A'):,}")
                    print(f"Likes: {stats.get('diggCount', 'N/A'):,}")
                    print(f"Comments: {stats.get('commentCount', 'N/A'):,}")
                    print(f"Shares: {stats.get('shareCount', 'N/A'):,}")
        
        else:
            print("No posts found or unexpected response structure")
            print(f"Response keys: {list(posts_data.keys())}")
            
    else:
        print("❌ User not found in search results")
        print(f"Search response: {json.dumps(search_data, indent=2)[:500]}...")

except ValidationException as e:
    print(f"❌ Validation Error: {e}, Field: {e.field}")

except ResponseException as e:
    print(f"❌ Response Error: {e}, Status Code: {e.response.status_code}")
    print(f"Response: {e.response.text[:200]}...")

except Exception as e:
    print(f"❌ General Error: {e}")

print(f"\n{'='*60}")
print("Test completed!")