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
            cmd = f'echo {repr(request_json)} | API_TOKEN={self.brightdata_token} PRO_MODE=true npx @brightdata/mcp'
            
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
            
            # IMPORTANT: Despite the confusing naming from Bright Data:
            # - top_videos = RECENT posts (chronologically ordered) with playcount values
            # - top_posts_data = TOP PERFORMING posts (by engagement) for content enrichment
            # We use top_videos for recent post stats, top_posts_data for content analysis
            
            # Note: Content database saving moved to screening script
            # This allows the screening script to control when/how to save
            top_posts_data = profile_data.get('top_posts_data', [])
            
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
            
            # Convert posts data - use top_videos for recent posts with view counts
            posts = []
            
            # Get both fields from Bright Data response
            top_videos = profile_data.get('top_videos', [])  # Recent posts (chronological)
            top_posts_data = profile_data.get('top_posts_data', [])  # Top performing posts
            
            if top_videos:
                # Process recent videos from top_videos (has view counts)
                for video in top_videos[:post_count]:
                    video_id = video.get('video_id', '')
                    tiktok_url = video.get('video_url', '')
                    if not tiktok_url and video_id:
                        tiktok_url = f"https://www.tiktok.com/@{username}/video/{video_id}"
                    
                    # Parse create_date from Bright Data format
                    # Format: "Tue Aug 19 2025 14:13:00 GMT+0000 (Coordinated Universal Time)"
                    create_time = 0
                    formatted_date = 'Unknown'
                    create_date_str = video.get('create_date', '')
                    if create_date_str:
                        try:
                            # Remove the timezone description in parentheses
                            if 'GMT' in create_date_str:
                                date_part = create_date_str.split(' GMT')[0] + ' GMT'
                                # Parse the date
                                from datetime import datetime
                                dt = datetime.strptime(date_part.replace(' GMT', ''), '%a %b %d %Y %H:%M:%S')
                                create_time = int(dt.timestamp())
                                formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            # Fallback to dateutil parser
                            try:
                                from dateutil import parser
                                dt = parser.parse(create_date_str)
                                create_time = int(dt.timestamp())
                                formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                pass
                    
                    post_data = {
                        'id': video_id,
                        'description': video.get('description', ''),
                        'create_time': create_time,
                        'formatted_date': formatted_date,
                        'duration': 0,
                        'is_photo_post': False,  # top_videos are videos
                        'content_type': 'video',
                        'tiktok_url': tiktok_url,
                        'stats': {
                            'views': video.get('playcount', 0),  # Proper view counts from top_videos
                            'likes': video.get('diggcount', 0),
                            'comments': video.get('commentcount', 0),
                            'shares': video.get('share_count', 0)
                        }
                    }
                    
                    posts.append(post_data)
            elif top_posts_data:
                # Fallback: Use top_posts_data if no top_videos (rare case)
                # WARNING: top_posts_data doesn't have view counts (playcount=0)
                for post in top_posts_data[:post_count]:
                    post_id = post.get('post_id', '')
                    tiktok_url = post.get('post_url', '')
                    if not tiktok_url and post_id:
                        tiktok_url = f"https://www.tiktok.com/@{username}/video/{post_id}"
                    
                    # Parse create_time
                    create_time = 0
                    formatted_date = 'Unknown'
                    create_time_str = post.get('create_time', '')
                    if create_time_str:
                        try:
                            from dateutil import parser
                            dt = parser.parse(create_time_str)
                            create_time = int(dt.timestamp())
                            formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    
                    post_data = {
                        'id': post_id,
                        'description': post.get('description', ''),
                        'create_time': create_time,
                        'formatted_date': formatted_date,
                        'duration': 0,
                        'is_photo_post': post.get('post_type') == 'photo',
                        'content_type': post.get('post_type', 'video'),
                        'tiktok_url': tiktok_url,
                        'stats': {
                            'views': 0,  # top_posts_data doesn't have view counts
                            'likes': post.get('likes', 0),
                            'comments': 0,
                            'shares': 0
                        }
                    }
                    
                    posts.append(post_data)
            
            return {
                'success': True,
                'profile': profile,
                'posts': posts,
                'top_posts_data': profile_data.get('top_posts_data', [])  # Include top_posts_data in response
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
    BRIGHTDATA_TOKEN = "ddbb0138-fb46-4f00-a9f9-ce085a84dbce"
    
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