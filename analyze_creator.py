"""
Complete Creator Analysis Workflow
Combines TikAPI + TikTok MCP + LLM Analysis
"""
from tikapi_client import TikAPIClient
from tiktok_mcp_client import SimpleTikTokMCPClient
import json

class CreatorAnalyzer:
    def __init__(self, tikapi_key):
        self.tikapi_client = TikAPIClient(tikapi_key)
        self.mcp_client = SimpleTikTokMCPClient()
    
    def analyze_creator(self, username, post_count=5, extract_subtitles=True):
        """
        Complete creator analysis workflow
        
        Args:
            username: TikTok creator username
            post_count: Number of recent posts to analyze
            extract_subtitles: Whether to extract subtitles (requires API credits)
            
        Returns:
            dict: Complete analysis results
        """
        print(f"🔍 Analyzing creator: @{username}")
        print("=" * 60)
        
        # Step 1: Get creator profile and posts
        print("1. Fetching creator data...")
        creator_data = self.tikapi_client.get_creator_analysis(username, post_count)
        
        if not creator_data['success']:
            return {
                'success': False,
                'error': f"Failed to get creator data: {creator_data['error']}"
            }
        
        profile = creator_data['profile']
        posts = creator_data['posts']
        
        print(f"✅ Profile: {profile['nickname']} (@{profile['username']})")
        print(f"   Followers: {profile['followers']:,}")
        print(f"   Posts analyzed: {len(posts)}")
        
        # Step 2: Extract subtitles if requested
        subtitle_results = []
        if extract_subtitles:
            print(f"\n2. Extracting subtitles from {len(posts)} posts...")
            
            for i, post in enumerate(posts, 1):
                print(f"   Processing post {i}/{len(posts)}...")
                
                subtitle_result = self.mcp_client.extract_subtitles(post['tiktok_url'])
                
                if subtitle_result['success']:
                    print(f"   ✅ Subtitles extracted ({len(subtitle_result['subtitles'])} chars)")
                    subtitle_results.append({
                        'post_id': post['id'],
                        'subtitles': subtitle_result['subtitles'],
                        'success': True
                    })
                else:
                    error_msg = subtitle_result['error']
                    if 'Insufficient credits' in error_msg:
                        print(f"   ⚠️  API credits needed for subtitle extraction")
                    else:
                        print(f"   ❌ Failed: {error_msg}")
                    
                    subtitle_results.append({
                        'post_id': post['id'],
                        'error': error_msg,
                        'success': False
                    })
        else:
            print("2. Skipping subtitle extraction")
        
        # Step 3: Analyze content patterns
        print(f"\n3. Analyzing content patterns...")
        content_analysis = self._analyze_content_patterns(posts, subtitle_results)
        
        # Step 4: Generate creator summary
        print(f"\n4. Generating creator summary...")
        summary = self._generate_creator_summary(profile, posts, content_analysis)
        
        return {
            'success': True,
            'profile': profile,
            'posts': posts,
            'subtitle_results': subtitle_results,
            'content_analysis': content_analysis,
            'summary': summary
        }
    
    def _analyze_content_patterns(self, posts, subtitle_results):
        """Analyze content patterns from posts and subtitles"""
        
        # Analyze post descriptions
        descriptions = [post['description'] for post in posts if post['description']]
        
        # Extract hashtags
        all_hashtags = []
        for desc in descriptions:
            hashtags = [word for word in desc.split() if word.startswith('#')]
            all_hashtags.extend(hashtags)
        
        # Count hashtag frequency
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        
        # Analyze engagement patterns
        total_views = sum(post['stats']['views'] for post in posts)
        total_likes = sum(post['stats']['likes'] for post in posts)
        avg_engagement_rate = (total_likes / total_views * 100) if total_views > 0 else 0
        
        # Analyze subtitle content (if available)
        subtitle_analysis = {}
        successful_subtitles = [r for r in subtitle_results if r['success']]
        
        if successful_subtitles:
            all_subtitle_text = ' '.join([r['subtitles'] for r in successful_subtitles])
            subtitle_analysis = {
                'total_subtitle_chars': len(all_subtitle_text),
                'posts_with_subtitles': len(successful_subtitles),
                'average_subtitle_length': len(all_subtitle_text) / len(successful_subtitles)
            }
        
        return {
            'hashtags': {
                'unique_count': len(hashtag_counts),
                'most_common': sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                'total_used': len(all_hashtags)
            },
            'engagement': {
                'total_views': total_views,
                'total_likes': total_likes,
                'avg_engagement_rate': round(avg_engagement_rate, 2),
                'avg_views_per_post': total_views // len(posts) if posts else 0
            },
            'content_themes': self._extract_content_themes(descriptions),
            'subtitle_analysis': subtitle_analysis
        }
    
    def _extract_content_themes(self, descriptions):
        """Extract common themes from post descriptions"""
        # Simple keyword analysis
        common_themes = {
            'travel': ['travel', 'trip', 'vacation', 'hotel', 'flight', 'airport', 'city'],
            'food': ['food', 'restaurant', 'eat', 'dinner', 'lunch', 'breakfast', 'recipe'],
            'lifestyle': ['life', 'daily', 'routine', 'home', 'style', 'fashion'],
            'business': ['business', 'work', 'entrepreneur', 'money', 'brand', 'company'],
            'entertainment': ['fun', 'party', 'music', 'dance', 'comedy', 'funny']
        }
        
        theme_scores = {}
        all_text = ' '.join(descriptions).lower()
        
        for theme, keywords in common_themes.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                theme_scores[theme] = score
        
        return sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
    
    def _generate_creator_summary(self, profile, posts, content_analysis):
        """Generate a comprehensive creator summary"""
        
        # Top hashtags
        top_hashtags = [tag for tag, count in content_analysis['hashtags']['most_common'][:5]]
        
        # Top themes
        top_themes = [theme for theme, score in content_analysis['content_themes'][:3]]
        
        # Performance metrics
        engagement = content_analysis['engagement']
        
        summary = {
            'creator_type': self._classify_creator_type(profile, content_analysis),
            'content_focus': top_themes,
            'signature_hashtags': top_hashtags,
            'audience_size': profile['followers'],
            'engagement_rate': engagement['avg_engagement_rate'],
            'posting_consistency': self._analyze_posting_frequency(posts),
            'content_quality_indicators': {
                'avg_views': engagement['avg_views_per_post'],
                'hashtag_strategy': len(content_analysis['hashtags']['most_common']),
                'description_completeness': len([p for p in posts if p['description']]) / len(posts) * 100
            }
        }
        
        return summary
    
    def _classify_creator_type(self, profile, content_analysis):
        """Classify the type of creator based on content and engagement"""
        followers = profile['followers']
        themes = dict(content_analysis['content_themes'])
        
        # Size classification
        if followers < 10000:
            size = "micro"
        elif followers < 100000:
            size = "mid-tier"
        elif followers < 1000000:
            size = "macro"
        else:
            size = "mega"
        
        # Content classification
        if 'travel' in themes and themes['travel'] > 2:
            content_type = "travel"
        elif 'food' in themes and themes['food'] > 2:
            content_type = "food"
        elif 'lifestyle' in themes and themes['lifestyle'] > 2:
            content_type = "lifestyle"
        elif 'business' in themes and themes['business'] > 2:
            content_type = "business"
        else:
            content_type = "general"
        
        return f"{size}-{content_type}"
    
    def _analyze_posting_frequency(self, posts):
        """Analyze posting frequency and consistency"""
        if len(posts) < 2:
            return "insufficient_data"
        
        # This is a simplified analysis - in real implementation,
        # you'd analyze actual time gaps between posts
        return "regular"  # Could be: "daily", "weekly", "irregular", "regular"


# Example usage
if __name__ == "__main__":
    API_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    
    analyzer = CreatorAnalyzer(API_KEY)
    
    # Test with a creator
    result = analyzer.analyze_creator("8jelly8", post_count=3, extract_subtitles=True)
    
    if result['success']:
        print("\n" + "=" * 60)
        print("📊 CREATOR ANALYSIS RESULTS")
        print("=" * 60)
        
        profile = result['profile']
        summary = result['summary']
        
        print(f"\n👤 Creator: {profile['nickname']} (@{profile['username']})")
        print(f"📈 Followers: {profile['followers']:,}")
        print(f"🎯 Creator Type: {summary['creator_type']}")
        print(f"💪 Engagement Rate: {summary['engagement_rate']}%")
        
        print(f"\n🏷️  Top Hashtags: {', '.join(summary['signature_hashtags'])}")
        print(f"🎨 Content Themes: {', '.join(summary['content_focus'])}")
        
        print(f"\n📱 Content Analysis:")
        print(f"   • Posts analyzed: {len(result['posts'])}")
        print(f"   • Avg views per post: {summary['content_quality_indicators']['avg_views']:,}")
        print(f"   • Description completeness: {summary['content_quality_indicators']['description_completeness']:.1f}%")
        
        subtitle_success = len([r for r in result['subtitle_results'] if r['success']])
        print(f"   • Subtitles extracted: {subtitle_success}/{len(result['subtitle_results'])}")
        
    else:
        print(f"❌ Analysis failed: {result['error']}")