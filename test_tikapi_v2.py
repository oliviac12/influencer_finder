import requests
import json

# TikAPI configuration
API_KEY = "ELH1bxax9M1fDRQtVjwy7utCxFI6ufizQYaGQyLNNZy5O1sZ"

# Test different possible base URLs
base_urls = [
    "https://api.tikapi.io",
    "https://tikapi.io/api",
    "https://api.tikapi.io/v1",
]

test_username = "27travels"

print(f"Testing TikAPI with creator: {test_username}")
print("=" * 50)

for base_url in base_urls:
    print(f"\nTrying base URL: {base_url}")
    
    # Try different header formats
    header_variants = [
        {"X-API-KEY": API_KEY},
        {"Authorization": f"Bearer {API_KEY}"},
        {"apikey": API_KEY},
        {"api-key": API_KEY},
    ]
    
    for headers in header_variants:
        headers["Content-Type"] = "application/json"
        
        # Test a simple endpoint first
        test_endpoints = [
            "/public/posts",
            "/public/profile", 
            "/health",
            "/",
        ]
        
        for endpoint in test_endpoints:
            url = base_url + endpoint
            try:
                # Try GET
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code != 404:
                    print(f"  ✓ {endpoint} (GET) - Status: {response.status_code}")
                    if response.status_code == 200:
                        print(f"    Response: {response.text[:100]}...")
                        print(f"    Headers used: {list(headers.keys())}")
                        
                        # If we found a working combination, try to get posts
                        if "public" in endpoint:
                            posts_url = base_url + "/public/posts"
                            params = {"username": test_username}
                            posts_resp = requests.get(posts_url, headers=headers, params=params)
                            print(f"    Posts attempt - Status: {posts_resp.status_code}")
                            if posts_resp.status_code == 200:
                                print("    SUCCESS! Found working endpoint")
                                print(f"    Response: {posts_resp.text[:200]}...")
                        break
                        
            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                continue

print("\n" + "=" * 50)
print("If none worked, we might need:")
print("1. Different API key format")
print("2. Account activation")
print("3. Different endpoint structure")
print("4. Check TikAPI dashboard for examples")