"""
Bulk Creator Performance Screening
Screen all creators in data.csv for recent engagement performance
"""
import pandas as pd
import csv
from tikapi_client import TikAPIClient
from datetime import datetime
import time

class CreatorScreener:
    def __init__(self, tikapi_key, min_avg_views=5000, max_days_since_last_post=60):
        self.tikapi_client = TikAPIClient(tikapi_key)
        self.min_avg_views = min_avg_views
        self.max_days_since_last_post = max_days_since_last_post
        self.qualified_creators = []
        self.failed_creators = []
    
    def screen_all_creators(self, csv_file="data.csv", output_file="qualified_creators.csv"):
        """Screen all creators from CSV file"""
        
        print(f"🔍 Creator Performance Screening")
        print(f"Minimum average views required: {self.min_avg_views:,}")
        print(f"Maximum days since last post: {self.max_days_since_last_post}")
        print("=" * 60)
        
        # Read creator data
        try:
            df = pd.read_csv(csv_file)
            creators = df.to_dict('records')
            print(f"📊 Loading {len(creators)} creators from {csv_file}")
        except Exception as e:
            print(f"❌ Error reading {csv_file}: {e}")
            return
        
        # Screen each creator
        for i, creator in enumerate(creators, 1):
            username = creator['username']
            print(f"\n[{i}/{len(creators)}] Screening @{username}...")
            
            result = self.screen_creator(username, creator)
            
            if result['qualified']:
                self.qualified_creators.append(result)
                print(f"✅ QUALIFIED - Avg: {result['avg_views']:,} views, {result['days_since_last_post']} days ago")
            else:
                self.failed_creators.append(result)
                if result['error']:
                    print(f"❌ ERROR - {result['error']}")
                else:
                    print(f"❌ FAILED - {result['failure_reason']}")
            
            # Small delay to avoid rate limiting
            time.sleep(2)
        
        # Save results
        self.save_results(output_file)
        self.print_summary()
    
    def screen_creator(self, username, creator_info):
        """Screen individual creator"""
        try:
            # Get creator posts
            result = self.tikapi_client.get_creator_analysis(username, post_count=8)
            
            if not result['success']:
                return {
                    'username': username,
                    'qualified': False,
                    'error': result['error'],
                    'original_data': creator_info
                }
            
            profile = result['profile']
            all_posts = result['posts']
            
            # Filter recent posts (excluding potential pinned posts)
            recent_posts = self._filter_recent_posts(all_posts, 5)
            
            # Calculate metrics
            avg_views = self._calculate_average_views(recent_posts)
            total_engagement = sum(
                post['stats']['likes'] + post['stats']['comments'] + post['stats']['shares'] 
                for post in recent_posts
            )
            avg_engagement = total_engagement // len(recent_posts) if recent_posts else 0
            
            # Check recency of most recent post
            most_recent_post = recent_posts[0] if recent_posts else None
            days_since_last_post = None
            
            if most_recent_post:
                from datetime import datetime
                current_time = datetime.now()
                last_post_time = datetime.fromtimestamp(most_recent_post['create_time'])
                days_since_last_post = (current_time - last_post_time).days
            
            # Determine if qualified (both criteria must be met)
            meets_view_threshold = avg_views >= self.min_avg_views
            meets_recency_threshold = days_since_last_post is not None and days_since_last_post <= self.max_days_since_last_post
            qualified = meets_view_threshold and meets_recency_threshold
            
            # Determine failure reason
            failure_reason = None
            if not meets_view_threshold and not meets_recency_threshold:
                failure_reason = f"Low views ({avg_views:,}) AND stale ({days_since_last_post} days old)"
            elif not meets_view_threshold:
                failure_reason = f"Low views ({avg_views:,})"
            elif not meets_recency_threshold:
                failure_reason = f"Stale content ({days_since_last_post} days since last post)"
            
            return {
                'username': username,
                'nickname': profile['nickname'],
                'followers': profile['followers'],
                'total_posts_analyzed': len(recent_posts),
                'avg_views': avg_views,
                'avg_engagement': avg_engagement,
                'days_since_last_post': days_since_last_post,
                'qualified': qualified,
                'error': None,
                'failure_reason': failure_reason,
                'original_data': creator_info,
                'recent_posts': [
                    {
                        'id': post['id'],
                        'description': post['description'][:100] + '...' if len(post['description']) > 100 else post['description'],
                        'views': post['stats']['views'],
                        'likes': post['stats']['likes'],
                        'comments': post['stats']['comments'],
                        'date': post['formatted_date'],
                        'tiktok_url': post['tiktok_url']
                    }
                    for post in recent_posts[:5]  # Store top 5 recent posts
                ]
            }
            
        except Exception as e:
            return {
                'username': username,
                'qualified': False,
                'error': f"Unexpected error: {str(e)}",
                'original_data': creator_info
            }
    
    def _filter_recent_posts(self, posts, count=5):
        """Filter to get most recent posts"""
        # Sort by creation time (most recent first)
        sorted_posts = sorted(posts, key=lambda x: x.get('create_time', 0), reverse=True)
        return sorted_posts[:count]
    
    def _calculate_average_views(self, posts):
        """Calculate average views"""
        if not posts:
            return 0
        total_views = sum(post['stats']['views'] for post in posts)
        return total_views // len(posts)
    
    def save_results(self, output_file):
        """Save qualified creators to CSV"""
        if not self.qualified_creators:
            print(f"\n⚠️  No qualified creators found!")
            return
        
        # Prepare data for CSV
        csv_data = []
        for creator in self.qualified_creators:
            # Flatten recent posts data
            row = {
                'username': creator['username'],
                'nickname': creator['nickname'],
                'followers': creator['followers'],
                'avg_views': creator['avg_views'],
                'avg_engagement': creator['avg_engagement'],
                'total_posts_analyzed': creator['total_posts_analyzed'],
                'original_email': creator['original_data'].get('email', ''),
                'original_bio_link': creator['original_data'].get('bio_link', ''),
                'original_region': creator['original_data'].get('region', ''),
            }
            
            # Add recent post details (up to 5 posts)
            for i, post in enumerate(creator['recent_posts'][:5], 1):
                row[f'post{i}_views'] = post['views']
                row[f'post{i}_likes'] = post['likes']
                row[f'post{i}_description'] = post['description']
                row[f'post{i}_url'] = post['tiktok_url']
                row[f'post{i}_date'] = post['date']
            
            csv_data.append(row)
        
        # Save to CSV
        try:
            df = pd.DataFrame(csv_data)
            df.to_csv(output_file, index=False)
            print(f"\n💾 Saved {len(csv_data)} qualified creators to {output_file}")
        except Exception as e:
            print(f"\n❌ Error saving to {output_file}: {e}")
    
    def print_summary(self):
        """Print screening summary"""
        total = len(self.qualified_creators) + len(self.failed_creators)
        
        print(f"\n{'='*60}")
        print(f"📊 SCREENING SUMMARY")
        print(f"{'='*60}")
        failed_no_error = [c for c in self.failed_creators if not c['error']]
        low_views = [c for c in failed_no_error if 'Low views' in c.get('failure_reason', '')]
        stale_content = [c for c in failed_no_error if 'Stale content' in c.get('failure_reason', '')]
        both_issues = [c for c in failed_no_error if 'AND' in c.get('failure_reason', '')]
        
        print(f"Total creators screened: {total}")
        print(f"✅ Qualified creators: {len(self.qualified_creators)}")
        print(f"❌ Low views only: {len(low_views)}")
        print(f"⏰ Stale content only: {len(stale_content)}")
        print(f"💥 Both low views & stale: {len(both_issues)}")
        print(f"🔥 API errors: {len([c for c in self.failed_creators if c['error']])}")
        
        if self.qualified_creators:
            print(f"\n🎯 QUALIFIED CREATORS:")
            for creator in sorted(self.qualified_creators, key=lambda x: x['avg_views'], reverse=True):
                print(f"   • @{creator['username']} - {creator['avg_views']:,} avg views ({creator['followers']:,} followers)")
        
        if self.failed_creators:
            failed_no_error = [c for c in self.failed_creators if not c['error']]
            if failed_no_error:
                print(f"\n📉 FAILED CREATORS:")
                for creator in sorted(failed_no_error, key=lambda x: x.get('avg_views', 0), reverse=True):
                    reason = creator.get('failure_reason', 'Unknown reason')
                    print(f"   • @{creator['username']} - {reason}")


if __name__ == "__main__":
    API_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    
    # Initialize screener with 5K view threshold and 60-day recency filter
    screener = CreatorScreener(API_KEY, min_avg_views=5000, max_days_since_last_post=60)
    
    # Screen all creators
    screener.screen_all_creators("data.csv", "qualified_creators.csv")
    
    print(f"\n🚀 Screening complete! Check 'qualified_creators.csv' for results.")