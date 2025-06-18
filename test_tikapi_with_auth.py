import requests
import json

# TikAPI configuration
API_KEY = "ELH1bxax9M1fDRQtVjwy7utCxFI6ufizQYaGQyLNNZy5O1sZ"
BASE_URL = "https://api.tikapi.io"

# Test with first creator from our sample
test_username = "27travels"

print(f"Testing TikAPI with creator: {test_username}")
print("=" * 50)

# Headers with API key (common patterns)
headers = {
    "X-API-KEY": API_KEY,  # Common pattern 1
    "Authorization": f"Bearer {API_KEY}",  # Common pattern 2
    "Content-Type": "application/json"
}

# Try to get user profile
def get_user_profile(username):
    """Get user profile information"""
    # Try different endpoint patterns
    endpoints = [
        f"/public/profile?username={username}",
        f"/public/user?username={username}",
        f"/user/info?username={username}",
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        try:
            response = requests.get(
                BASE_URL + endpoint,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    return None

# Try to get user posts
def get_user_posts(username, count=5):
    """Get recent posts from user"""
    # Common endpoint patterns for posts
    endpoints = [
        f"/public/posts?username={username}&count={count}",
        f"/user/posts?username={username}&count={count}",
        f"/public/user/posts?username={username}&count={count}",
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        try:
            response = requests.get(
                BASE_URL + endpoint,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error: {e}")
    
    return None

# Test the functions
if API_KEY == "YOUR_API_KEY_HERE":
    print("\n⚠️  Please update the API_KEY variable with your actual TikAPI key!")
    print("You can get one at: https://tikapi.io")
else:
    print("\n1. Testing profile fetch...")
    profile = get_user_profile(test_username)
    
    if profile:
        print(f"\n✅ Successfully fetched profile!")
        print(json.dumps(profile, indent=2)[:500] + "...")
    
    print("\n2. Testing posts fetch...")
    posts = get_user_posts(test_username)
    
    if posts:
        print(f"\n✅ Successfully fetched posts!")
        print(f"Number of posts returned: {len(posts) if isinstance(posts, list) else 'N/A'}")
        print(json.dumps(posts, indent=2)[:500] + "...")