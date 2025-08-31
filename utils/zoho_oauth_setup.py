"""
Zoho OAuth Setup Helper
Helps obtain OAuth credentials for Zoho Mail API
"""
import webbrowser
import urllib.parse
import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler to capture OAuth callback"""
    
    def do_GET(self):
        # Parse the authorization code from callback
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            self.server.auth_code = params['code'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1 style="color: #4CAF50;">✅ Authorization Successful!</h1>
                <p>You can now close this window and return to your terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
        else:
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = """
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1 style="color: #f44336;">❌ Authorization Failed</h1>
                <p>No authorization code received. Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass


def setup_zoho_oauth():
    """Interactive setup for Zoho OAuth credentials"""
    
    print("=" * 60)
    print("🔐 ZOHO OAUTH SETUP WIZARD")
    print("=" * 60)
    print()
    
    print("This wizard will help you obtain OAuth credentials for Zoho Mail API.")
    print("You'll need to have already created an application in Zoho API Console.")
    print()
    
    print("📝 STEP 1: Create Zoho Application")
    print("-" * 40)
    print("1. Go to: https://api-console.zoho.com/")
    print("2. Click 'Add Client'")
    print("3. Choose 'Server-based Applications'")
    print("4. Enter these details:")
    print("   - Client Name: Influencer Finder")
    print("   - Homepage URL: http://localhost:8080")
    print("   - Authorized Redirect URI: http://localhost:8080/callback")
    print()
    
    input("Press Enter when you've created the application...")
    print()
    
    print("📝 STEP 2: Enter Client Credentials")
    print("-" * 40)
    client_id = input("Enter your Client ID: ").strip()
    client_secret = input("Enter your Client Secret: ").strip()
    print()
    
    print("📝 STEP 3: Choose Data Center")
    print("-" * 40)
    print("Select your Zoho data center:")
    print("1. COM (zoho.com) - Default")
    print("2. EU (zoho.eu)")
    print("3. IN (zoho.in)")
    print("4. AU (zoho.com.au)")
    print("5. JP (zoho.jp)")
    
    dc_choice = input("Enter choice (1-5) [1]: ").strip() or "1"
    
    dc_map = {
        "1": "com",
        "2": "eu",
        "3": "in",
        "4": "com.au",
        "5": "jp"
    }
    
    data_center = dc_map.get(dc_choice, "com")
    auth_domain = f"https://accounts.zoho.{data_center}"
    
    print(f"Using data center: {auth_domain}")
    print()
    
    print("📝 STEP 4: Authorize Application")
    print("-" * 40)
    
    # Required scopes
    scopes = "ZohoMail.messages.ALL,ZohoMail.accounts.READ"
    
    # Build authorization URL
    auth_url = f"{auth_domain}/oauth/v2/auth"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": scopes,
        "redirect_uri": "http://localhost:8080/callback",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    auth_url_full = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    print("Opening browser for authorization...")
    print("If browser doesn't open, visit this URL:")
    print(auth_url_full)
    print()
    
    # Start local server to capture callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None
    
    # Run server in background thread
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url_full)
    
    # Wait for callback
    print("Waiting for authorization...")
    timeout = 60  # 60 seconds timeout
    start_time = time.time()
    
    while server.auth_code is None and (time.time() - start_time) < timeout:
        time.sleep(0.5)
    
    if server.auth_code:
        print("✅ Authorization code received!")
        print()
        
        print("📝 STEP 5: Exchange Code for Tokens")
        print("-" * 40)
        
        # Exchange authorization code for tokens
        token_url = f"{auth_domain}/oauth/v2/token"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "http://localhost:8080/callback",
            "code": server.auth_code
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code == 200:
            tokens = response.json()
            refresh_token = tokens.get("refresh_token")
            
            print("✅ Tokens obtained successfully!")
            print()
            
            # Get account ID
            print("📝 STEP 6: Get Account ID")
            print("-" * 40)
            
            access_token = tokens.get("access_token")
            headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
            
            api_domain = f"https://mail.zoho.{data_center}"
            account_url = f"{api_domain}/api/accounts"
            
            response = requests.get(account_url, headers=headers)
            
            if response.status_code == 200:
                accounts = response.json()
                if accounts.get("data"):
                    account_id = accounts["data"][0]["accountId"]
                    email_address = accounts["data"][0]["emailAddress"]
                    
                    print(f"✅ Found account: {email_address}")
                    print(f"   Account ID: {account_id}")
                    print()
                    
                    print("=" * 60)
                    print("🎉 SETUP COMPLETE!")
                    print("=" * 60)
                    print()
                    print("Add these lines to your .env file:")
                    print()
                    print("# Zoho OAuth (for native scheduling)")
                    print(f"ZOHO_CLIENT_ID={client_id}")
                    print(f"ZOHO_CLIENT_SECRET={client_secret}")
                    print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
                    print(f"ZOHO_ACCOUNT_ID={account_id}")
                    print(f"ZOHO_DATA_CENTER={data_center}")
                    print()
                    
                    # Offer to save to file
                    save = input("Would you like to append these to .env? (y/n): ").strip().lower()
                    if save == 'y':
                        with open('../.env', 'a') as f:
                            f.write("\n# Zoho OAuth (for native scheduling)\n")
                            f.write(f"ZOHO_CLIENT_ID={client_id}\n")
                            f.write(f"ZOHO_CLIENT_SECRET={client_secret}\n")
                            f.write(f"ZOHO_REFRESH_TOKEN={refresh_token}\n")
                            f.write(f"ZOHO_ACCOUNT_ID={account_id}\n")
                            f.write(f"ZOHO_DATA_CENTER={data_center}\n")
                        print("✅ Credentials saved to .env file!")
                    
                else:
                    print("❌ No accounts found")
            else:
                print(f"❌ Failed to get account: {response.text}")
                
        else:
            print(f"❌ Failed to exchange code: {response.text}")
            
    else:
        print("❌ Authorization timeout - no code received")
    
    print()
    print("Setup wizard complete!")


if __name__ == "__main__":
    setup_zoho_oauth()