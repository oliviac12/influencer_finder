import requests
import json

# TikAPI configuration
API_KEY = "ELH1bxax9M1fDRQtVjwy7utCxFI6ufizQYaGQyLNNZy5O1sZ"
BASE_URL = "https://api.tikapi.io"

# Test username
test_username = "27travels"

print(f"Testing TikAPI with creator: {test_username}")
print("=" * 50)

# Based on the documentation link you provided, the endpoint should be:
# https://api.tikapi.io/public/posts

headers = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# First, we need to get the user's secUid
# Try to search for the user first
search_url = f"{BASE_URL}/public/search"
search_params = {
    "keyword": test_username,
    "type": "user"
}

print("1. Searching for user to get secUid...")
try:
    response = requests.get(search_url, headers=headers, params=search_params)
    print(f"Search Status: {response.status_code}")
    if response.status_code == 200:
        search_data = response.json()
        print("Search successful!")
        # Usually the first result is the exact match
        if search_data.get("users") and len(search_data["users"]) > 0:
            user = search_data["users"][0]
            sec_uid = user.get("secUid")
            print(f"Found user: {user.get('uniqueId')} with secUid: {sec_uid}")
            
            # Now get posts using secUid
            posts_url = f"{BASE_URL}/public/posts"
            posts_params = {
                "secUid": sec_uid,
                "count": 5
            }
            
            print("\n2. Getting user posts...")
            posts_response = requests.get(posts_url, headers=headers, params=posts_params)
            print(f"Posts Status: {posts_response.status_code}")
            
            if posts_response.status_code == 200:
                posts_data = posts_response.json()
                print(f"\n✅ Successfully fetched posts!")
                
                if "itemList" in posts_data:
                    print(f"Number of posts: {len(posts_data['itemList'])}")
                    for i, post in enumerate(posts_data['itemList'][:3]):
                        print(f"\nPost {i+1}:")
                        print(f"  ID: {post.get('id')}")
                        print(f"  Description: {post.get('desc', '')[:100]}...")
                        print(f"  Create Time: {post.get('createTime')}")
                        if 'stats' in post:
                            print(f"  Views: {post['stats'].get('playCount', 'N/A')}")
                            print(f"  Likes: {post['stats'].get('diggCount', 'N/A')}")
            else:
                print(f"Posts Error: {posts_response.text}")
    else:
        print(f"Search Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")

# Also try the direct approach with username
print("\n" + "=" * 50)
print("3. Trying direct username approach...")

# According to docs, might need to convert username to secUid first
# Let's try the profile endpoint with different auth approach
profile_url = f"{BASE_URL}/public/profile"
try:
    response = requests.post(
        profile_url,
        headers=headers,
        json={"username": test_username}
    )
    print(f"Profile Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except Exception as e:
    print(f"Error: {e}")