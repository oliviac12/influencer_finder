"""
Hybrid Creator Data Client - TikAPI + Bright Data MCP Fallback
Provides unified interface for fetching creator data with automatic fallback
Now saves content data (captions, hashtags) to creators_content_database.json
"""
import subprocess
import json
import time
import sys
import os
from datetime import datetime
from .tikapi_client import TikAPIClient

# Add utils to path for content database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.content_database import ContentDatabase


class CreatorDataClient:
    def __init__(self, tikapi_key, brightdata_token, prefer_brightdata=True):
        self.tikapi = TikAPIClient(tikapi_key)
        self.brightdata_token = brightdata_token
        self.prefer_brightdata = prefer_brightdata
        self.content_db = ContentDatabase()
    
    def get_creator_analysis(self, username, post_count=35):
        """
        Get creator analysis with automatic fallback
        
        Args:
            username: TikTok username (without @)
            post_count: Number of posts to fetch
            
        Returns:
            dict: Success status, profile data, and posts data (TikAPI-compatible format)
        """
        # Try preferred service first
        if self.prefer_brightdata:
            pass  # Trying Bright Data MCP
            brightdata_result = self._get_brightdata_analysis(username, post_count)
            
            if brightdata_result['success']:
                pass  # Bright Data MCP success
                return brightdata_result
            else:
                # Always fall back to TikAPI when Bright Data MCP fails, regardless of error type
                pass  # Bright Data failed, falling back to TikAPI
                return self._try_tikapi_fallback(username, post_count)
        else:
            # TikAPI first, then Bright Data fallback
            pass  # Trying TikAPI
            tikapi_result = self._try_tikapi_fallback(username, post_count)
            
            if tikapi_result['success']:
                return tikapi_result
            else:
                pass  # TikAPI failed, falling back to Bright Data
                return self._get_brightdata_analysis(username, post_count)
    
    def _try_tikapi_fallback(self, username, post_count):
        """Try TikAPI with proper error handling"""
        tikapi_result = self.tikapi.get_creator_analysis(username, post_count)
        
        if tikapi_result['success']:
            pass  # TikAPI success
            return tikapi_result
        else:
            pass  # TikAPI failed
            return tikapi_result
    
    def _get_brightdata_analysis(self, username, post_count=35):
        """
        Get creator analysis using Bright Data MCP
        
        Args:
            username: TikTok username (without @)
            post_count: Number of posts to fetch
            
        Returns:
            dict: Success status, profile data, and posts data (TikAPI-compatible format)
        """
        try:
            # Prepare JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "web_data_tiktok_profiles",
                    "arguments": {"url": f"https://www.tiktok.com/@{username}"}
                }
            }
            # Use echo + pipe approach that works
            request_json = json.dumps(request)
            cmd = f'echo {repr(request_json)} | API_TOKEN={self.brightdata_token} npx @brightdata/mcp'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180  # 3 minutes timeout for MCP
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Bright Data MCP failed: {result.stderr[:200]}"
                }
            
            # Parse the response - look for the result line (ignore progress notifications)
            lines = result.stdout.strip().split('\n')
            profile_data = None
            
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    parsed = json.loads(line)
                    
                    # Skip progress notifications
                    if parsed.get('method') == 'notifications/progress':
                        continue
                    
                    # Look for the actual result
                    if 'result' in parsed and 'content' in parsed['result']:
                        content = parsed['result']['content'][0]['text']
                        
                        # Handle building status response
                        try:
                            status_check = json.loads(content)
                            if isinstance(status_check, dict) and status_check.get('status') == 'building':
                                return {
                                    'success': False,
                                    'error': f"Bright Data is building snapshot: {status_check.get('message', 'try again later')}"
                                }
                        except:
                            pass
                        
                        # Parse the actual profile data
                        profiles = json.loads(content)
                        if isinstance(profiles, list) and len(profiles) > 0:
                            profile_data = profiles[0]
                            break
                            
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
            
            if not profile_data:
                return {
                    'success': False,
                    'error': "Could not parse Bright Data MCP response"
                }
            
            # Save content data to database (NEW)
            top_posts_data = profile_data.get('top_posts_data', [])
            if top_posts_data:
                try:
                    self.content_db.save_creator_content(username, profile_data, top_posts_data)
                except Exception as e:
                    print(f"   ⚠️  Warning: Failed to save content data for @{username}: {e}")
            
            # Convert to TikAPI-compatible format
            profile = {
                'username': profile_data.get('account_id', username),
                'nickname': profile_data.get('nickname', ''),
                'signature': profile_data.get('biography', ''),
                'followers': profile_data.get('followers', 0),
                'following': profile_data.get('following', 0),
                'videos': profile_data.get('videos_count', 0),
                'verified': profile_data.get('is_verified', False),
                'sec_uid': profile_data.get('secu_id', '')
            }
            
            # Convert posts data
            posts = []
            top_videos = profile_data.get('top_videos', [])
            
            for video in top_videos[:post_count]:
                # Convert timestamp
                create_time = 0
                formatted_date = 'Unknown'
                if 'create_date' in video:
                    try:
                        date_str = video['create_date']
                        if 'GMT' in date_str:
                            date_part = date_str.split(' GMT')[0]
                            dt = datetime.strptime(date_part, "%a %b %d %Y %H:%M:%S")
                            create_time = int(dt.timestamp())
                            formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                # Get TikTok URL
                tiktok_url = video.get('video_url', '')
                if not tiktok_url:
                    video_id = video.get('video_id', '')
                    if video_id:
                        tiktok_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                
                post_data = {
                    'id': video.get('video_id', ''),
                    'description': video.get('description', ''),
                    'create_time': create_time,
                    'formatted_date': formatted_date,
                    'duration': 0,  # Bright Data doesn't provide duration
                    'is_photo_post': False,  # Assume videos from top_videos
                    'content_type': 'video',
                    'tiktok_url': tiktok_url,
                    'stats': {
                        'views': video.get('playcount', 0),
                        'likes': video.get('diggcount', 0),
                        'comments': video.get('commentcount', 0),
                        'shares': video.get('share_count', 0)
                    }
                }
                
                posts.append(post_data)
            
            return {
                'success': True,
                'profile': profile,
                'posts': posts
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "Bright Data MCP timeout (3 minutes)"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Bright Data MCP error: {str(e)}"
            }
    
    def set_tikapi_preferred(self):
        """Switch to TikAPI-first strategy"""
        self.prefer_brightdata = False
        print("🔥 Switched to TikAPI-first strategy")
    
    def set_brightdata_preferred(self):
        """Switch to Bright Data-first strategy"""
        self.prefer_brightdata = True
        print("🌐 Switched to Bright Data-first strategy")


# Test function
if __name__ == "__main__":
    # Test with both API keys
    TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    BRIGHTDATA_TOKEN = "36c74962-d03a-41c1-b261-7ea4109ec8bd"
    
    client = CreatorDataClient(TIKAPI_KEY, BRIGHTDATA_TOKEN)
    
    # Test with a username
    test_username = "doriany1394"
    
    print(f"🧪 Testing Hybrid Creator Data Client")
    print(f"📋 Testing username: @{test_username}")
    print("=" * 70)
    
    # Test the hybrid system (will use TikAPI unless it fails)
    result = client.get_creator_analysis(test_username, post_count=5)
    
    if result['success']:
        profile = result['profile']
        posts = result['posts']
        
        print(f"\n✅ Final result: Retrieved profile and {len(posts)} posts")
        print(f"   Profile: @{profile['username']} ({profile['nickname']})")
        print(f"   Followers: {profile['followers']:,}")
        print(f"   Videos: {profile['videos']:,}")
        
        print(f"\n📱 Recent posts:")
        for i, post in enumerate(posts[:3], 1):
            print(f"{i}. {post['description'][:60]}...")
            print(f"   Views: {post['stats']['views']:,} | Likes: {post['stats']['likes']:,}")
            print(f"   Date: {post['formatted_date']}")
            print(f"   URL: {post['tiktok_url']}")
            print()
    else:
        print(f"❌ Final result: {result['error']}")
    
    print("=" * 70)
    print("🎯 Hybrid client test complete!")