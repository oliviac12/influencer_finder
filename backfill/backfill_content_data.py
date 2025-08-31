"""
Backfill Content Data Script
Extracts content data (captions, hashtags) from all existing CSV files
Only focuses on top_posts_data - no shoppable filtering or complex processing
"""
import pandas as pd
import csv
import json
import os
import subprocess
import time
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.content_database import ContentDatabase


class ContentBackfiller:
    def __init__(self, tikapi_key, brightdata_token):
        self.tikapi_key = tikapi_key
        self.brightdata_token = brightdata_token
        self.content_db = ContentDatabase()
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
    
    def get_all_creators_from_csvs(self, input_dir="data/inputs/"):
        """Get all unique creator usernames from CSV files"""
        all_creators = set()
        csv_files = []
        
        # Find all CSV files
        for filename in os.listdir(input_dir):
            if filename.endswith('.csv'):
                csv_files.append(os.path.join(input_dir, filename))
        
        print(f"📁 Found {len(csv_files)} CSV files:")
        for csv_file in csv_files:
            print(f"   - {os.path.basename(csv_file)}")
        
        # Extract usernames from each CSV
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                # Assume username column is named 'username' or 'Username'
                username_cols = [col for col in df.columns if 'username' in col.lower()]
                
                if username_cols:
                    username_col = username_cols[0]
                    usernames = df[username_col].dropna().unique()
                    all_creators.update(usernames)
                    print(f"   📋 {os.path.basename(csv_file)}: {len(usernames)} creators")
                else:
                    print(f"   ⚠️  No username column found in {os.path.basename(csv_file)}")
                    
            except Exception as e:
                print(f"   ❌ Error reading {csv_file}: {e}")
        
        return list(all_creators)
    
    def extract_content_brightdata(self, username):
        """Extract content data using Bright Data MCP"""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "web_data_tiktok_profiles",
                    "arguments": {"url": f"https://www.tiktok.com/@{username}"}
                }
            }
            request_json = json.dumps(request)
            cmd = f'echo {repr(request_json)} | API_TOKEN={self.brightdata_token} PRO_MODE=true npx @brightdata/mcp'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout
            )
            
            if result.returncode != 0:
                return None, f"MCP failed: {result.stderr[:100]}"
            
            # Parse response
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    parsed = json.loads(line)
                    
                    if parsed.get('method') == 'notifications/progress':
                        continue
                    
                    if 'result' in parsed and 'content' in parsed['result']:
                        content = parsed['result']['content'][0]['text']
                        
                        # Handle building status
                        try:
                            status_check = json.loads(content)
                            if isinstance(status_check, dict) and status_check.get('status') == 'building':
                                return None, f"Building snapshot: {status_check.get('message', 'try again later')}"
                        except:
                            pass
                        
                        profiles = json.loads(content)
                        if isinstance(profiles, list) and len(profiles) > 0:
                            profile_data = profiles[0]
                            top_posts_data = profile_data.get('top_posts_data', [])
                            return (profile_data, top_posts_data), None
                            
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
            
            return None, "Could not parse MCP response"
            
        except subprocess.TimeoutExpired:
            return None, "MCP timeout (3 minutes)"
        except Exception as e:
            return None, f"MCP error: {str(e)}"
    
    def extract_content_tikapi(self, username):
        """Fallback to TikAPI - but we can't get top_posts_data from TikAPI"""
        # TikAPI doesn't have top_posts_data equivalent with captions/hashtags
        # We could potentially extract some data but it won't have the same structure
        return None, "TikAPI fallback not implemented for content extraction"
    
    def backfill_creator(self, username):
        """Backfill content data for a single creator"""
        # Check if already exists
        if self.content_db.creator_exists(username):
            print(f"   ⏭️  @{username} already exists, skipping")
            self.skipped_count += 1
            return True
        
        print(f"   🌐 Extracting content for @{username}...")
        
        # Try Bright Data MCP first
        data, error = self.extract_content_brightdata(username)
        
        if data is None:
            print(f"   ❌ Failed to get content for @{username}: {error}")
            self.failed_count += 1
            return False
        
        profile_data, top_posts_data = data
        
        if not top_posts_data:
            print(f"   ⚠️  No posts data for @{username}")
            self.failed_count += 1
            return False
        
        # Save to content database
        try:
            self.content_db.save_creator_content(username, profile_data, top_posts_data)
            print(f"   ✅ Saved @{username}: {len(top_posts_data)} posts")
            self.processed_count += 1
            return True
        except Exception as e:
            print(f"   ❌ Failed to save @{username}: {e}")
            self.failed_count += 1
            return False
    
    def run_backfill(self, input_dir="data/inputs/", max_creators=None):
        """Run the backfill process"""
        print("🚀 Starting Content Data Backfill")
        print("=" * 60)
        
        # Get all creators
        all_creators = self.get_all_creators_from_csvs(input_dir)
        
        if max_creators:
            all_creators = all_creators[:max_creators]
        
        print(f"\n📊 Total unique creators to process: {len(all_creators)}")
        
        # Get database stats before starting
        initial_stats = self.content_db.get_stats()
        print(f"📁 Current database: {initial_stats['creator_count']} creators")
        
        print(f"\n🔄 Processing creators...")
        print("=" * 60)
        
        start_time = time.time()
        
        for i, username in enumerate(all_creators, 1):
            print(f"\n[{i}/{len(all_creators)}] Processing @{username}")
            
            self.backfill_creator(username)
            
            # Rate limiting - 2 second delay between requests
            if i < len(all_creators):
                time.sleep(2)
            
            # Progress update every 10 creators
            if i % 10 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print(f"\n📈 Progress: {i}/{len(all_creators)} ({i/len(all_creators)*100:.1f}%)")
                print(f"   ⏱️  Rate: {rate:.1f} creators/min")
                print(f"   ✅ Processed: {self.processed_count}")
                print(f"   ⏭️  Skipped: {self.skipped_count}")
                print(f"   ❌ Failed: {self.failed_count}")
        
        # Final summary
        elapsed = time.time() - start_time
        print(f"\n" + "=" * 60)
        print("🏁 Backfill Complete!")
        print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"✅ Successfully processed: {self.processed_count}")
        print(f"⏭️  Skipped (already exists): {self.skipped_count}")
        print(f"❌ Failed: {self.failed_count}")
        
        # Final database stats
        final_stats = self.content_db.get_stats()
        print(f"📁 Final database: {final_stats['creator_count']} creators, {final_stats['total_posts']} posts")


if __name__ == "__main__":
    # API keys
    TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    BRIGHTDATA_TOKEN = "ddbb0138-fb46-4f00-a9f9-ce085a84dbce"
    
    # Initialize backfiller
    backfiller = ContentBackfiller(TIKAPI_KEY, BRIGHTDATA_TOKEN)
    
    # Run backfill - limit to 10 creators for testing
    print("🧪 Running backfill with 10 creators for testing...")
    backfiller.run_backfill(max_creators=10)
    
    print("\n💡 To run full backfill, remove the max_creators parameter")