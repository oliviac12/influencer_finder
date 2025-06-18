"""
TikAPI Client - Reusable module for TikTok creator data fetching
"""
import sys
from datetime import datetime

try:
    from tikapi import TikAPI, ValidationException, ResponseException
except ImportError:
    print("Installing TikAPI SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tikapi"])
    from tikapi import TikAPI, ValidationException, ResponseException


class TikAPIClient:
    def __init__(self, api_key):
        self.api = TikAPI(api_key)
    
    def get_creator_profile(self, username):
        """Get creator profile information"""
        try:
            response = self.api.public.check(username=username)
            if response.status_code == 200:
                data = response.json()
                user_info = data.get('userInfo', {})
                user = user_info.get('user', {})
                stats = user_info.get('stats', {})
                
                return {
                    'success': True,
                    'username': user.get('uniqueId'),
                    'nickname': user.get('nickname'),
                    'sec_uid': user.get('secUid'),
                    'followers': stats.get('followerCount', 0),
                    'following': stats.get('followingCount', 0),
                    'videos': stats.get('videoCount', 0),
                    'signature': user.get('signature', ''),
                    'verified': user.get('verified', False)
                }
            else:
                return {
                    'success': False,
                    'error': f"Profile check failed: {response.status_code}",
                    'details': response.text[:200]
                }
                
        except (ValidationException, ResponseException) as e:
            return {
                'success': False,
                'error': f"API Error: {str(e)}",
                'details': getattr(e, 'response', {}).get('text', '')[:200] if hasattr(e, 'response') else ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def get_recent_posts(self, sec_uid, count=10):
        """Get recent posts for a creator using their secUid"""
        try:
            response = self.api.public.posts(secUid=sec_uid)
            if response.status_code == 200:
                data = response.json()
                posts = data.get('itemList', [])
                
                processed_posts = []
                for post in posts[:count]:
                    # Detect if this is a photo carousel vs video
                    is_photo_post = 'imagePost' in post
                    duration = post.get('video', {}).get('duration', 0) if not is_photo_post else 0
                    
                    post_data = {
                        'id': post.get('id'),
                        'description': post.get('desc', ''),
                        'create_time': post.get('createTime'),
                        'formatted_date': self._format_timestamp(post.get('createTime')),
                        'duration': duration,
                        'is_photo_post': is_photo_post,
                        'content_type': 'photo_carousel' if is_photo_post else 'video',
                        'video_url': post.get('video', {}).get('playAddr', '') if not is_photo_post else '',
                        'download_url': post.get('video', {}).get('downloadAddr', '') if not is_photo_post else '',
                        'stats': {
                            'views': post.get('stats', {}).get('playCount', 0),
                            'likes': post.get('stats', {}).get('diggCount', 0),
                            'comments': post.get('stats', {}).get('commentCount', 0),
                            'shares': post.get('stats', {}).get('shareCount', 0)
                        }
                    }
                    
                    # Add photo-specific data if it's a photo post
                    if is_photo_post:
                        image_post = post['imagePost']
                        post_data['photo_count'] = len(image_post.get('images', []))
                        post_data['photo_urls'] = [
                            img['imageURL']['urlList'][0] if img.get('imageURL', {}).get('urlList') else ''
                            for img in image_post.get('images', [])
                        ]
                    
                    processed_posts.append(post_data)
                
                return {
                    'success': True,
                    'posts': processed_posts,
                    'total_available': len(data.get('itemList', []))
                }
            else:
                return {
                    'success': False,
                    'error': f"Posts fetch failed: {response.status_code}",
                    'details': response.text[:200]
                }
                
        except (ValidationException, ResponseException) as e:
            return {
                'success': False,
                'error': f"API Error: {str(e)}",
                'details': getattr(e, 'response', {}).get('text', '')[:200] if hasattr(e, 'response') else ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}"
            }
    
    def get_tiktok_url(self, username, post_id):
        """Generate TikTok URL for a post"""
        return f"https://www.tiktok.com/@{username}/video/{post_id}"
    
    def _format_timestamp(self, timestamp):
        """Format Unix timestamp to readable date"""
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return 'Unknown'
        return 'Unknown'
    
    def get_creator_analysis(self, username, post_count=5):
        """Complete workflow: get profile + recent posts"""
        # Get profile
        profile = self.get_creator_profile(username)
        if not profile['success']:
            return profile
        
        # Get posts
        posts = self.get_recent_posts(profile['sec_uid'], post_count)
        if not posts['success']:
            return {
                'success': False,
                'error': f"Failed to get posts: {posts['error']}",
                'profile': profile
            }
        
        # Add TikTok URLs to posts
        for post in posts['posts']:
            post['tiktok_url'] = self.get_tiktok_url(username, post['id'])
        
        return {
            'success': True,
            'profile': profile,
            'posts': posts['posts'],
            'total_posts_available': posts['total_available']
        }


# Example usage
if __name__ == "__main__":
    # Test the client
    API_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    client = TikAPIClient(API_KEY)
    
    result = client.get_creator_analysis("8jelly8", post_count=3)
    
    if result['success']:
        profile = result['profile']
        print(f"✅ {profile['nickname']} (@{profile['username']})")
        print(f"   Followers: {profile['followers']:,}")
        print(f"   Recent posts: {len(result['posts'])}")
        
        for i, post in enumerate(result['posts'], 1):
            print(f"\n{i}. {post['description'][:50]}...")
            print(f"   URL: {post['tiktok_url']}")
            print(f"   Views: {post['stats']['views']:,}")
    else:
        print(f"❌ Error: {result['error']}")