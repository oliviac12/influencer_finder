import requests

# Based on the documentation URL pattern, let's test the exact endpoint
API_KEY = "ELH1bxax9M1fDRQtVjwy7utCxFI6ufizQYaGQyLNNZy5O1sZ"

# The documentation shows: https://tikapi.io/documentation/#tag/Public/operation/public.posts
# So the API might be at tikapi.io not api.tikapi.io

print("Testing TikAPI connection...")
print("=" * 50)

# Test 1: Direct documentation URL
url = "https://tikapi.io/api/public/posts"
headers = {
    "X-API-KEY": API_KEY,
}

print(f"Testing: {url}")
try:
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: With parameters
print("\n" + "-" * 50)
print("Testing with username parameter...")

params = {
    "username": "27travels",
    "count": 1
}

try:
    response = requests.get(url, headers=headers, params=params)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 401:
        print("\n⚠️  Authentication issue. The API key might need to be:")
        print("1. Activated in your TikAPI dashboard")
        print("2. Used with a different header name")
        print("3. Associated with a paid plan")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 50)
print("Check your TikAPI dashboard at https://tikapi.io for:")
print("1. API key status")
print("2. Example code snippets")
print("3. Rate limits or plan restrictions")