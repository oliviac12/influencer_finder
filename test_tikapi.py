import requests
import json

# TikAPI endpoint
BASE_URL = "https://api.tikapi.io"

# Test with first creator from our sample
test_username = "27travels"

print(f"Testing TikAPI with creator: {test_username}")
print("=" * 50)

# First, let's try to get profile info without auth to see what happens
profile_endpoint = f"{BASE_URL}/public/profile"

try:
    # Try without any auth first
    response = requests.get(
        profile_endpoint,
        params={"username": test_username}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:500]}...")  # First 500 chars
    
    if response.status_code == 401:
        print("\nNeed API key. Please sign up at https://tikapi.io")
        print("Once you have an API key, we'll update this script.")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("Next steps:")
print("1. Go to https://tikapi.io and sign up for free trial")
print("2. Get your API key from the dashboard")
print("3. We'll update this script with proper authentication")