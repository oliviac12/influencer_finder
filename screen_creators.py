"""
Bulk Creator Performance Screening
Screen all creators in data.csv for recent video engagement performance
- Filters out photo carousel posts (focuses on video content only)
- Requires 3+ recent video posts for analysis
- Triple criteria: 5K+ avg views AND posted within 60 days AND has shoppable content
"""
import pandas as pd
import csv
import json
import os
from clients.tikapi_client import TikAPIClient
from clients.creator_data_client import CreatorDataClient
from utils.filter_shoppable import ShoppableContentFilter
from datetime import datetime
import time

class CreatorScreener:
    def __init__(self, tikapi_key, min_avg_views=5000, max_days_since_last_post=60, brightdata_token=None):
        # Use hybrid client if Bright Data token provided, otherwise TikAPI only
        if brightdata_token:
            self.data_client = CreatorDataClient(tikapi_key, brightdata_token)
            print("🔄 Using hybrid client: TikAPI + Bright Data MCP fallback")
        else:
            self.data_client = TikAPIClient(tikapi_key)
            print("🔥 Using TikAPI client only")
        self.shoppable_filter = ShoppableContentFilter()
        self.min_avg_views = min_avg_views
        self.max_days_since_last_post = max_days_since_last_post
        self.qualified_creators = []
        self.failed_creators = []
        
        # Data collection dataframes
        self.creator_lookup_data = []
        self.creator_post_lookup_data = []
        
        # Caching - will be set per dataset in screen_all_creators()
        self.cache_dir = None
        self.creator_cache = {}
        self.shoppable_cache = {}
        self.existing_creators = set()
    
    def screen_all_creators(self, csv_file="data/inputs/radar_5k_quitmyjob.csv", output_file=None):
        """Screen all creators from CSV file"""
        
        # Generate timestamped output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            input_basename = os.path.basename(csv_file).replace('.csv', '')
            output_file = f"data/outputs/{timestamp}_{input_basename}_qualified_creators.csv"
        
        # Setup dataset-specific cache and logging
        input_basename = os.path.basename(csv_file).replace('.csv', '')
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Update cache directory to be dataset-specific
        self.cache_dir = f"cache/screening/{input_basename}_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Reload caches for this specific dataset
        self.creator_cache = self._load_creator_cache()
        self.shoppable_cache = self._load_shoppable_cache()
        self.existing_creators = self._load_existing_creators()
        
        # Setup dataset-specific log file
        log_file = f"logs/{timestamp}_{input_basename}_screening.log"
        os.makedirs("logs", exist_ok=True)
        print(f"📋 Logs: {log_file}")
        
        # Store log file path for potential use
        self.current_log_file = log_file
        
        print(f"🔍 Creator Performance Screening with Triple Filtering")
        print(f"📁 Input: {csv_file}")
        print(f"📁 Output: {output_file}")
        print(f"Filter 1 - Must have shoppable content in recent posts")
        print(f"Filter 2 - Minimum average views: {self.min_avg_views:,}")
        print(f"Filter 3 - Maximum days since last post: {self.max_days_since_last_post}")
        print("=" * 70)
        
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
            
            # Skip if creator already fully processed
            if username in self.existing_creators:
                print(f"   ⏭️ Skipping - already processed in previous run")
                continue
            
            result = self.screen_creator(username, creator)
            
            if result['qualified']:
                self.qualified_creators.append(result)
                shoppable_info = f", {result['shoppable_posts_found']} shoppable posts"
                photo_filter_info = f" ({result['photo_posts_filtered']} photos filtered)" if result.get('photo_posts_filtered', 0) > 0 else ""
                print(f"✅ QUALIFIED - Avg: {result['avg_views']:,} views, {result['days_since_last_post']} days ago{shoppable_info}{photo_filter_info}")
            else:
                self.failed_creators.append(result)
                if result['error']:
                    print(f"❌ ERROR - {result['error']}")
                    
                    # Check for rate limit errors and stop processing
                    if 'rate-limit' in result['error'].lower() or 'rate limit' in result['error'].lower():
                        print(f"\n🚨 RATE LIMIT DETECTED - Stopping processing to preserve API credits")
                        print(f"📊 Processed {i}/{len(creators)} creators before hitting rate limit")
                        print(f"✅ Found {len(self.qualified_creators)} qualified creators so far")
                        
                        # Save current progress
                        self.save_results(output_file)
                        self.save_dataframes()
                        self._save_caches()
                        self.print_summary()
                        
                        print(f"\n⏰ You can resume processing later when rate limits reset (24h window)")
                        print(f"💡 The system will automatically skip the {i-1} already processed creators")
                        return  # Early exit from the method
                else:
                    print(f"❌ FAILED - {result['failure_reason']}")
            
            # Save caches incrementally after each creator (every 5 creators to avoid too much I/O)
            if i % 5 == 0:
                self._save_caches()
            
            # Increased delay to avoid rate limiting
            time.sleep(5)
        
        # Save results
        self.save_results(output_file)
        self.save_dataframes()
        self._save_caches()
        self.print_summary()
    
    def screen_creator(self, username, creator_info):
        """Screen individual creator with triple filtering"""
        try:
            # Check cache first
            if username in self.creator_cache:
                print(f"   📋 Using cached data for @{username}")
                result = self.creator_cache[username]
            else:
                # Get creator posts (fetch extra to account for filtering)
                result = self.data_client.get_creator_analysis(username, post_count=35)
                # Cache the result immediately after successful API call
                if result['success']:
                    self.creator_cache[username] = result
                    # Save immediately for this creator to prevent loss on timeout
                    try:
                        with open(os.path.join(self.cache_dir, "creator_cache.json"), 'w') as f:
                            json.dump(self.creator_cache, f, indent=2)
                    except Exception as e:
                        print(f"   Warning: Could not save creator cache: {e}")
            
            if not result['success']:
                return {
                    'username': username,
                    'qualified': False,
                    'error': result['error'],
                    'original_data': creator_info
                }
            
            profile = result['profile']
            all_posts = result['posts']
            
            # Collect creator profile data for creator_lookup dataframe
            creator_lookup_row = {
                'username': profile['username'],
                'nickname': profile['nickname'],
                'bio': profile['signature'],
                'follower_count': profile['followers'],
                'following_count': profile['following'],
                'video_count': profile['videos'],
                'verified': profile['verified'],
                'sec_uid': profile['sec_uid']
            }
            self.creator_lookup_data.append(creator_lookup_row)
            
            # Filter to get 28 most recent posts (excluding potential pinned posts)
            recent_posts = self._filter_recent_posts(all_posts, 28)
            
            # Filter 1: Check for shoppable content in recent posts FIRST
            print(f"   🛍️ Filter 1: Checking shoppable content in {len(recent_posts)} recent posts...")
            shoppable_posts = []
            
            # Check each recent post for shoppable content (early exit after finding 1)
            for i, post in enumerate(recent_posts, 1):  # Check up to 28 recent posts
                if post.get('tiktok_url'):
                    print(f"   Checking post {i}/{len(recent_posts)}...", end=" ")
                    
                    # Check cache first
                    url = post['tiktok_url']
                    if url in self.shoppable_cache:
                        is_shoppable = self.shoppable_cache[url]
                        print(f"📋", end=" ")
                    else:
                        is_shoppable = self.shoppable_filter.check_tiktok_commission_eligible(url)
                        self.shoppable_cache[url] = is_shoppable
                        # Save shoppable cache immediately after each check
                        try:
                            with open(os.path.join(self.cache_dir, "shoppable_cache.json"), 'w') as f:
                                json.dump(self.shoppable_cache, f, indent=2)
                        except Exception as e:
                            print(f"   Warning: Could not save shoppable cache: {e}")
                    
                    # Collect post data for creator_post_lookup dataframe (for posts we checked)
                    post_lookup_row = {
                        'url': post.get('tiktok_url', ''),
                        'creator_username': username,
                        'is_shoppable': is_shoppable,
                        'post_id': post.get('id', ''),
                        'description': post.get('description', ''),
                        'create_time': post.get('create_time', 0),
                        'formatted_date': post.get('formatted_date', ''),
                        'duration': post.get('duration', 0),
                        'is_photo_post': post.get('is_photo_post', False),
                        'content_type': post.get('content_type', 'video'),
                        'views': post.get('stats', {}).get('views', 0),
                        'likes': post.get('stats', {}).get('likes', 0),
                        'comments': post.get('stats', {}).get('comments', 0),
                        'shares': post.get('stats', {}).get('shares', 0)
                    }
                    self.creator_post_lookup_data.append(post_lookup_row)
                    
                    if is_shoppable:
                        shoppable_posts.append(post)
                        print(f"✅ Shoppable - Found! Skipping remaining posts.")
                        break  # Early exit after finding first shoppable post
                    else:
                        print(f"❌ Not shoppable")
            
            # Early exit if no shoppable content found
            if len(shoppable_posts) == 0:
                posts_checked = len(recent_posts)  # We checked all posts if none were shoppable
                return {
                    'username': username,
                    'qualified': False,
                    'error': None,
                    'failure_reason': "No shoppable content found",
                    'original_data': creator_info,
                    'recent_posts_checked': posts_checked,
                    'shoppable_posts_found': 0
                }
            
            posts_checked = i  # i is the last post number we checked
            print(f"   ✅ Filter 1 PASSED: Found {len(shoppable_posts)} shoppable posts (checked {posts_checked}/{len(recent_posts)} posts)")
            
            # Filter 2: Check engagement metrics
            print(f"   📊 Filter 2: Checking engagement metrics...")
            video_posts = [post for post in recent_posts if not post.get('is_photo_post', False)][:5]  # Only video posts for engagement calc
            
            # Calculate metrics using only video posts
            if len(video_posts) < 3:
                return {
                    'username': username,
                    'qualified': False,
                    'error': None,
                    'failure_reason': f"Insufficient video content ({len(video_posts)} videos, need 3+)",
                    'original_data': creator_info,
                    'recent_posts_checked': posts_checked,
                    'shoppable_posts_found': len(shoppable_posts)
                }
            
            avg_views = self._calculate_average_views(video_posts)
            total_engagement = sum(
                post['stats']['likes'] + post['stats']['comments'] + post['stats']['shares'] 
                for post in video_posts
            )
            avg_engagement = total_engagement // len(video_posts)
            
            meets_view_threshold = avg_views >= self.min_avg_views
            if not meets_view_threshold:
                return {
                    'username': username,
                    'qualified': False,
                    'error': None,
                    'failure_reason': f"Low views ({avg_views:,})",
                    'original_data': creator_info,
                    'recent_posts_checked': posts_checked,
                    'shoppable_posts_found': len(shoppable_posts),
                    'avg_views': avg_views
                }
            
            print(f"   ✅ Filter 2 PASSED: {avg_views:,} avg views (need {self.min_avg_views:,}+)")
            
            # Filter 3: Check recency
            print(f"   📅 Filter 3: Checking post recency...")
            most_recent_post = video_posts[0] if video_posts else None
            days_since_last_post = None
            
            if most_recent_post:
                from datetime import datetime
                current_time = datetime.now()
                last_post_time = datetime.fromtimestamp(most_recent_post['create_time'])
                days_since_last_post = (current_time - last_post_time).days
            
            meets_recency_threshold = days_since_last_post is not None and days_since_last_post <= self.max_days_since_last_post
            if not meets_recency_threshold:
                return {
                    'username': username,
                    'qualified': False,
                    'error': None,
                    'failure_reason': f"Stale content ({days_since_last_post} days since last post)",
                    'original_data': creator_info,
                    'recent_posts_checked': posts_checked,
                    'shoppable_posts_found': len(shoppable_posts),
                    'avg_views': avg_views,
                    'days_since_last_post': days_since_last_post
                }
            
            print(f"   ✅ Filter 3 PASSED: Last post {days_since_last_post} days ago (need {self.max_days_since_last_post}+ days max)")
            print(f"   🎉 ALL FILTERS PASSED - Creator qualifies!")
            
            # All three filters passed - creator is qualified
            qualified = True
            failure_reason = None
            
            return {
                'username': username,
                'nickname': profile['nickname'],
                'followers': profile['followers'],
                'total_posts_analyzed': len(video_posts),
                'video_posts_found': len(video_posts),
                'photo_posts_filtered': len(recent_posts) - len(video_posts),
                'recent_posts_checked': len(recent_posts[:10]),
                'shoppable_posts_found': len(shoppable_posts),
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
                        'tiktok_url': post['tiktok_url'],
                        'content_type': post.get('content_type', 'video')
                    }
                    for post in video_posts[:5]  # Store top 5 recent video posts only
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
                'video_posts_analyzed': creator['total_posts_analyzed'],
                'photo_posts_filtered': creator.get('photo_posts_filtered', 0),
                'recent_posts_checked': creator.get('recent_posts_checked', 0),
                'shoppable_posts_found': creator.get('shoppable_posts_found', 0),
                'days_since_last_post': creator.get('days_since_last_post', 'N/A'),
                'original_email': creator['original_data'].get('email', ''),
                'original_bio_link': creator['original_data'].get('bio_link', ''),
                'original_region': creator['original_data'].get('region', ''),
            }
            
            # Add recent post details (up to 5 video posts only)
            for i, post in enumerate(creator['recent_posts'][:5], 1):
                row[f'post{i}_views'] = post['views']
                row[f'post{i}_likes'] = post['likes']
                row[f'post{i}_description'] = post['description']
                row[f'post{i}_url'] = post['tiktok_url']
                row[f'post{i}_date'] = post['date']
                row[f'post{i}_content_type'] = post.get('content_type', 'video')
            
            csv_data.append(row)
        
        # Save to CSV
        try:
            df = pd.DataFrame(csv_data)
            df.to_csv(output_file, index=False)
            print(f"\n💾 Saved {len(csv_data)} qualified creators to {output_file}")
        except Exception as e:
            print(f"\n❌ Error saving to {output_file}: {e}")
    
    def save_dataframes(self):
        """Save creator_lookup and creator_post_lookup dataframes (cumulative across runs)"""
        try:
            # Save creator_lookup dataframe (append to existing)
            if self.creator_lookup_data:
                new_creator_df = pd.DataFrame(self.creator_lookup_data)
                
                # Load existing data if file exists
                if os.path.exists('creator_lookup.csv'):
                    existing_creator_df = pd.read_csv('creator_lookup.csv')
                    # Combine and remove duplicates (keep latest)
                    combined_creator_df = pd.concat([existing_creator_df, new_creator_df], ignore_index=True)
                    combined_creator_df = combined_creator_df.drop_duplicates(subset=['username'], keep='last')
                else:
                    combined_creator_df = new_creator_df
                
                combined_creator_df.to_csv('creator_lookup.csv', index=False)
                print(f"💾 Saved {len(combined_creator_df)} total creator profiles to creator_lookup.csv ({len(self.creator_lookup_data)} new)")
            
            # Save creator_post_lookup dataframe (append to existing)
            if self.creator_post_lookup_data:
                new_posts_df = pd.DataFrame(self.creator_post_lookup_data)
                
                # Load existing data if file exists
                if os.path.exists('creator_post_lookup.csv'):
                    existing_posts_df = pd.read_csv('creator_post_lookup.csv')
                    # Combine and remove duplicates (keep latest)
                    combined_posts_df = pd.concat([existing_posts_df, new_posts_df], ignore_index=True)
                    combined_posts_df = combined_posts_df.drop_duplicates(subset=['url'], keep='last')
                else:
                    combined_posts_df = new_posts_df
                
                combined_posts_df.to_csv('creator_post_lookup.csv', index=False)
                print(f"💾 Saved {len(combined_posts_df)} total posts to creator_post_lookup.csv ({len(self.creator_post_lookup_data)} new)")
                
        except Exception as e:
            print(f"❌ Error saving dataframes: {e}")
    
    def _load_creator_cache(self):
        """Load creator data cache"""
        cache_file = os.path.join(self.cache_dir, "creator_cache.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_shoppable_cache(self):
        """Load shoppable content cache"""
        cache_file = os.path.join(self.cache_dir, "shoppable_cache.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_caches(self):
        """Save both caches"""
        try:
            # Save creator cache
            with open(os.path.join(self.cache_dir, "creator_cache.json"), 'w') as f:
                json.dump(self.creator_cache, f, indent=2)
            
            # Save shoppable cache
            with open(os.path.join(self.cache_dir, "shoppable_cache.json"), 'w') as f:
                json.dump(self.shoppable_cache, f, indent=2)
                
            print(f"💾 Saved caches: {len(self.creator_cache)} creators, {len(self.shoppable_cache)} posts")
        except Exception as e:
            print(f"❌ Error saving caches: {e}")
    
    def _load_existing_creators(self):
        """Load existing creators from creator_lookup.csv to avoid reprocessing"""
        existing_creators = set()
        if os.path.exists('creator_lookup.csv'):
            try:
                df = pd.read_csv('creator_lookup.csv')
                existing_creators = set(df['username'].tolist())
                print(f"📋 Found {len(existing_creators)} existing creators to skip")
            except Exception as e:
                print(f"Warning: Could not load existing creators: {e}")
        return existing_creators
    
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
    TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    BRIGHTDATA_TOKEN = "36c74962-d03a-41c1-b261-7ea4109ec8bd"
    
    # Initialize screener with hybrid client (TikAPI + Bright Data fallback)
    screener = CreatorScreener(
        TIKAPI_KEY, 
        min_avg_views=5000, 
        max_days_since_last_post=60,
        brightdata_token=BRIGHTDATA_TOKEN
    )
    
    # Screen all creators
    screener.screen_all_creators("radar_1k_10K_fashion_affiliate_5%_eng_rate.csv", "qualified_creators.csv")
    
    print(f"\n🚀 Screening complete! Check 'qualified_creators.csv' for results.")