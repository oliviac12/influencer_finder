"""
Bulk Creator Data Collection
Screen all creators for shoppable content detection and cache data
- Filters out photo carousel posts (focuses on video content only)
- Caches creator and post data for downstream analysis
- Primary filter: Must have shoppable content in recent posts
"""
import pandas as pd
import csv
import json
import os
from clients.tikapi_client import TikAPIClient
from clients.creator_data_client import CreatorDataClient
from utils.filter_shoppable import ShoppableContentFilter
from utils.content_database import ContentDatabase
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class CreatorScreener:
    def __init__(self, tikapi_key, brightdata_token=None):
        # Use hybrid client if Bright Data token provided, otherwise TikAPI only
        if brightdata_token:
            self.data_client = CreatorDataClient(tikapi_key, brightdata_token)
            print("🔄 Using hybrid client: TikAPI + Bright Data MCP fallback")
        else:
            self.data_client = TikAPIClient(tikapi_key)
            print("🔥 Using TikAPI client only")
        self.shoppable_filter = ShoppableContentFilter()
        # Initialize content database for automatic saving
        self.content_db = ContentDatabase()
        # Note: engagement filtering removed - downstream processing handles view thresholds
        self.processed_creators = []
        self.failed_creators = []
        
        # Data collection dataframes
        self.creator_lookup_data = []
        self.creator_post_lookup_data = []
        
        # Caching - will be set per dataset in screen_all_creators()
        self.cache_dir = None
        self.creator_cache = {}
        self.shoppable_cache = {}
        self.invalid_usernames = set()
        self.existing_creators = set()
        
        # CSV modification tracking
        self.input_csv_file = None
        self.invalid_csv_file = None
        self.removed_usernames = []
    
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
        
        # Set up CSV modification tracking
        self.input_csv_file = csv_file
        self.invalid_csv_file = f"data/outputs/{input_basename}_invalid_usernames.csv"
        
        # Reload caches for this specific dataset
        self.creator_cache = self._load_creator_cache()
        self.shoppable_cache = self._load_shoppable_cache()
        self.invalid_usernames = self._load_invalid_usernames()
        self.existing_creators = self._load_existing_creators()
        
        # Setup dataset-specific log file
        log_file = f"logs/{timestamp}_{input_basename}_screening.log"
        os.makedirs("logs", exist_ok=True)
        print(f"📋 Logs: {log_file}")
        
        # Store log file path for potential use
        self.current_log_file = log_file
        
        print(f"🔍 Creator Data Collection with Shoppable Content Detection")
        print(f"📁 Input: {csv_file}")
        print(f"📁 Cache: {self.cache_dir}")
        print(f"Filter 1 - Must have shoppable content in recent posts")
        print(f"Note: Engagement filtering removed - handled in downstream processing")
        
        # Show cache status for better run expectations
        if len(self.existing_creators) > 0:
            print(f"📋 Cache Status: {len(self.existing_creators)} creators already processed")
            print(f"📋 Invalid usernames to skip: {len(self.invalid_usernames)}")
        
        print("=" * 70)
        
        # Read creator data
        try:
            df = pd.read_csv(csv_file)
            creators = df.to_dict('records')
            print(f"📊 Loading {len(creators)} creators from {csv_file}")
        except Exception as e:
            print(f"❌ Error reading {csv_file}: {e}")
            return
        
        # Use parallel processing for faster screening
        self._screen_creators_parallel(creators)
        
        # Save results
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
            
            # Filter 1: Check for shoppable content in recent posts FIRST (optimized with batch processing)
            print(f"   🛍️ Filter 1: Checking shoppable content in {len(recent_posts)} recent posts...")
            shoppable_posts = []
            
            # Get URLs to check (not in cache)
            urls_to_check = []
            cached_results = {}
            post_url_map = {}  # Map URLs to posts
            
            for post in recent_posts:
                if post.get('tiktok_url'):
                    url = post['tiktok_url']
                    post_url_map[url] = post
                    
                    if url in self.shoppable_cache:
                        cached_results[url] = self.shoppable_cache[url]
                    else:
                        urls_to_check.append(url)
            
            print(f"   📋 Found {len(cached_results)} cached results, checking {len(urls_to_check)} new URLs...")
            
            # Batch check uncached URLs
            new_results = {}
            if urls_to_check:
                # Check in smaller batches to find shoppable content quickly
                batch_size = min(5, len(urls_to_check))  # Check 5 URLs at a time
                
                for batch_start in range(0, len(urls_to_check), batch_size):
                    batch_urls = urls_to_check[batch_start:batch_start + batch_size]
                    print(f"   🔄 Batch checking {len(batch_urls)} URLs...")
                    
                    batch_results = self.shoppable_filter.check_batch_tiktok_commission_eligible(batch_urls)
                    new_results.update(batch_results)
                    
                    # Update cache with new results
                    self.shoppable_cache.update(batch_results)
                    
                    # Early exit if we found shoppable content
                    if any(batch_results.values()):
                        print(f"   ✅ Found shoppable content! Stopping batch checking.")
                        break
            
            # Combine all results
            all_results = {**cached_results, **new_results}
            
            # Process posts and collect data
            posts_checked = 0
            for post in recent_posts:
                url = post.get('tiktok_url')
                if not url or url not in all_results:
                    continue
                    
                posts_checked += 1
                is_shoppable = all_results[url]
                
                # Collect post data for creator_post_lookup dataframe
                post_lookup_row = {
                    'url': url,
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
                    print(f"   ✅ Found shoppable post: {url[:50]}...")
                    # Continue checking all posts to collect complete data
            
            # Save updated cache
            if new_results:
                try:
                    with open(os.path.join(self.cache_dir, "shoppable_cache.json"), 'w') as f:
                        json.dump(self.shoppable_cache, f, indent=2)
                except Exception as e:
                    print(f"   Warning: Could not save shoppable cache: {e}")
            
            # Early exit if no shoppable content found
            if len(shoppable_posts) == 0:
                return {
                    'username': username,
                    'qualified': False,
                    'error': None,
                    'failure_reason': "No shoppable content found",
                    'original_data': creator_info,
                    'recent_posts_checked': posts_checked,
                    'shoppable_posts_found': 0
                }
            
            print(f"   ✅ SHOPPABLE CONTENT FOUND: {len(shoppable_posts)} posts (checked {posts_checked}/{len(recent_posts)} posts)")
            print(f"   🎉 CREATOR PROCESSED - Data cached for downstream analysis!")
            
            # Calculate basic metrics for cache (no filtering applied)
            video_posts = [post for post in recent_posts if not post.get('is_photo_post', False)]
            avg_views = self._calculate_average_views(video_posts[:5]) if video_posts else 0
            total_engagement = sum(
                post['stats']['likes'] + post['stats']['comments'] + post['stats']['shares'] 
                for post in video_posts[:5]
            ) if video_posts else 0
            avg_engagement = total_engagement // len(video_posts[:5]) if video_posts else 0
            
            # Get recency data
            most_recent_post = video_posts[0] if video_posts else None
            days_since_last_post = None
            if most_recent_post:
                from datetime import datetime
                current_time = datetime.now()
                last_post_time = datetime.fromtimestamp(most_recent_post['create_time'])
                days_since_last_post = (current_time - last_post_time).days
            
            # Save to content database automatically
            if len(shoppable_posts) > 0:  # Only save qualified creators
                try:
                    # Prepare posts data for content database
                    posts_for_db = []
                    for post in video_posts[:30]:  # Save up to 30 posts
                        # Extract hashtags from description if not in separate field
                        description = post.get('description', '')
                        hashtags = post.get('hashtags', [])
                        if not hashtags and description:
                            # Extract hashtags from description
                            import re
                            hashtags = re.findall(r'#\w+', description)
                            hashtags = [tag.replace('#', '') for tag in hashtags]
                        
                        post_data = {
                            'id': post.get('id', ''),
                            'desc': description,  # Use description field directly
                            'create_time': post.get('create_time', 0),
                            'formatted_date': post.get('formatted_date', ''),
                            'duration': post.get('duration', 0),
                            'is_photo_post': post.get('is_photo_post', False),
                            'content_type': post.get('content_type', 'video'),
                            'tiktok_url': post.get('tiktok_url', ''),
                            'views': post.get('stats', {}).get('views', 0),
                            'likes': post.get('stats', {}).get('likes', 0),
                            'comments': post.get('stats', {}).get('comments', 0),
                            'shares': post.get('stats', {}).get('shares', 0),
                            'tags': hashtags
                        }
                        posts_for_db.append(post_data)
                    
                    # Save to content database
                    self.content_db.save_creator_content(
                        username=username,
                        profile_data={
                            'username': profile['username'],
                            'nickname': profile['nickname'],
                            'bio': profile.get('signature', ''),
                            'followers': profile['followers'],
                            'following': profile['following'],
                            'videos': profile['videos'],
                            'verified': profile['verified'],
                            'sec_uid': profile.get('sec_uid', ''),
                            'email': profile.get('email', '')  # Include email if extracted
                        },
                        top_posts_data=posts_for_db
                    )
                    print(f"   💾 Saved to content database")
                except Exception as e:
                    print(f"   ⚠️ Warning: Could not save to content database: {e}")
            
            # All creators with shoppable content are processed (no qualification filtering)
            qualified = True
            failure_reason = None
            
            return {
                'username': username,
                'nickname': profile['nickname'],
                'followers': profile['followers'],
                'total_posts_analyzed': len(video_posts),
                'video_posts_found': len(video_posts),
                'photo_posts_filtered': len(recent_posts) - len(video_posts),
                'recent_posts_checked': posts_checked,
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
        """Save all caches"""
        try:
            # Save creator cache
            with open(os.path.join(self.cache_dir, "creator_cache.json"), 'w') as f:
                json.dump(self.creator_cache, f, indent=2)
            
            # Save shoppable cache
            with open(os.path.join(self.cache_dir, "shoppable_cache.json"), 'w') as f:
                json.dump(self.shoppable_cache, f, indent=2)
            
            # Save invalid usernames cache
            self._save_invalid_usernames()
                
            print(f"💾 Saved caches: {len(self.creator_cache)} creators, {len(self.shoppable_cache)} posts, {len(self.invalid_usernames)} invalid")
        except Exception as e:
            print(f"❌ Error saving caches: {e}")
    
    def _load_invalid_usernames(self):
        """Load invalid usernames cache"""
        cache_file = os.path.join(self.cache_dir, "invalid_usernames.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                invalid_set = set(data)
                if invalid_set:
                    print(f"🚫 Found {len(invalid_set)} invalid usernames to skip")
                return invalid_set
            except Exception as e:
                print(f"Warning: Could not load invalid usernames cache: {e}")
        return set()
    
    def _save_invalid_usernames(self):
        """Save invalid usernames cache"""
        try:
            cache_file = os.path.join(self.cache_dir, "invalid_usernames.json")
            with open(cache_file, 'w') as f:
                json.dump(list(self.invalid_usernames), f, indent=2)
        except Exception as e:
            print(f"❌ Error saving invalid usernames cache: {e}")
    
    def _remove_username_from_input_csv(self, username, creator_data):
        """Remove username from input CSV and add to invalid CSV"""
        try:
            # Read current input CSV
            df = pd.read_csv(self.input_csv_file)
            
            # Add to invalid CSV first (before removing from input)
            invalid_data = creator_data.copy()
            invalid_data['removal_reason'] = 'Bright Data MCP timeout (3 minutes)'
            invalid_data['removal_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Create or append to invalid CSV
            if os.path.exists(self.invalid_csv_file):
                invalid_df = pd.read_csv(self.invalid_csv_file)
                invalid_df = pd.concat([invalid_df, pd.DataFrame([invalid_data])], ignore_index=True)
            else:
                invalid_df = pd.DataFrame([invalid_data])
            
            invalid_df.to_csv(self.invalid_csv_file, index=False)
            
            # Remove from input CSV
            df_filtered = df[df['username'] != username]
            
            # Only update the input CSV if we actually removed something
            if len(df_filtered) < len(df):
                df_filtered.to_csv(self.input_csv_file, index=False)
                self.removed_usernames.append(username)
                print(f"   ✅ Removed @{username} from {self.input_csv_file}")
                print(f"   📄 Added @{username} to {self.invalid_csv_file}")
                print(f"   📊 Input dataset now has {len(df_filtered)} creators (was {len(df)})")
            else:
                print(f"   ⚠️ Username @{username} not found in input CSV for removal")
                
        except Exception as e:
            print(f"   ❌ Error removing username from CSV: {e}")
    
    def _load_existing_creators(self):
        """Load existing creators from creator_cache.json to avoid reprocessing"""
        existing_creators = set()
        if self.cache_dir and os.path.exists(os.path.join(self.cache_dir, "creator_cache.json")):
            try:
                with open(os.path.join(self.cache_dir, "creator_cache.json"), 'r') as f:
                    cache_data = json.load(f)
                existing_creators = set(cache_data.keys())
                print(f"📋 Found {len(existing_creators)} existing creators to skip from cache")
            except Exception as e:
                print(f"Warning: Could not load existing creators from cache: {e}")
        return existing_creators
    
    def _screen_creators_parallel(self, creators):
        """Screen creators using parallel processing for better performance"""
        # Filter creators to process (skip already processed and invalid)
        creators_to_process = []
        for i, creator in enumerate(creators, 1):
            username = creator['username']
            
            if username in self.existing_creators:
                print(f"[{i}/{len(creators)}] ⏭️ @{username} - already processed")
                continue
                
            if username in self.invalid_usernames:
                print(f"[{i}/{len(creators)}] 🚫 @{username} - invalid username, skipping")
                continue
                
            creators_to_process.append((i, creator))
        
        if not creators_to_process:
            print("No new creators to process")
            return
        
        print(f"\n🚀 Processing {len(creators_to_process)} creators with parallel processing...")
        print(f"📊 Using 4 threads for optimal performance")
        
        # Thread-safe locks for shared data
        self._print_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        processed_count = 0
        
        # Process creators in parallel batches
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all tasks
            future_to_creator = {
                executor.submit(self._screen_creator_threadsafe, i, creator, len(creators)): (i, creator)
                for i, creator in creators_to_process
            }
            
            # Process completed tasks
            for future in as_completed(future_to_creator):
                i, creator = future_to_creator[future]
                processed_count += 1
                
                try:
                    result = future.result()
                    
                    if result:
                        with self._print_lock:
                            if result['qualified']:
                                self.processed_creators.append(result)
                                shoppable_info = f", {result['shoppable_posts_found']} shoppable posts"
                                photo_filter_info = f" ({result['photo_posts_filtered']} photos filtered)" if result.get('photo_posts_filtered', 0) > 0 else ""
                                print(f"✅ [{processed_count}/{len(creators_to_process)}] @{result['username']} QUALIFIED - Avg: {result['avg_views']:,} views{shoppable_info}{photo_filter_info}")
                            else:
                                self.failed_creators.append(result)
                                if result['error']:
                                    print(f"❌ [{processed_count}/{len(creators_to_process)}] @{result['username']} ERROR - {result['error']}")
                                    
                                    # Handle specific errors
                                    error_msg = result['error'].lower()
                                    if 'bright data mcp timeout (3 minutes)' in error_msg:
                                        print(f"   🗑️ Removing @{result['username']} from input dataset")
                                        self._remove_username_from_input_csv(result['username'], creator)
                                    elif any(phrase in error_msg for phrase in ['user not found', 'user doesn\'t exist', 'invalid user', 'not available']):
                                        self.invalid_usernames.add(result['username'])
                                        print(f"   🚫 Marking @{result['username']} as invalid")
                                else:
                                    print(f"❌ [{processed_count}/{len(creators_to_process)}] @{result['username']} FAILED - {result['failure_reason']}")
                
                except Exception as e:
                    with self._print_lock:
                        print(f"❌ [{processed_count}/{len(creators_to_process)}] Thread error processing @{creator['username']}: {e}")
                
                # Save caches periodically
                if processed_count % 10 == 0:
                    with self._cache_lock:
                        self._save_caches()
                        with self._print_lock:
                            print(f"💾 Progress saved: {processed_count}/{len(creators_to_process)} completed")
        
        # Final save
        self._save_caches()
        print(f"\n🎉 Parallel processing completed: {len(creators_to_process)} creators processed")
    
    def _screen_creator_threadsafe(self, index, creator, total_creators):
        """Thread-safe version of screen_creator with progress tracking"""
        username = creator['username']
        
        with self._print_lock:
            print(f"\n[{index}/{total_creators}] 🔄 Screening @{username}...")
        
        # Add small delay to avoid overwhelming APIs
        time.sleep(1)
        
        result = self.screen_creator(username, creator)
        return result

    def print_summary(self):
        """Print screening summary"""
        total = len(self.processed_creators) + len(self.failed_creators)
        
        print(f"\n{'='*60}")
        print(f"📊 DATA COLLECTION SUMMARY")
        print(f"{'='*60}")
        
        print(f"Total creators screened: {total}")
        print(f"✅ Processed creators (with shoppable content): {len(self.processed_creators)}")
        print(f"❌ No shoppable content: {len([c for c in self.failed_creators if 'No shoppable content' in c.get('failure_reason', '')])}")
        print(f"🔥 API errors: {len([c for c in self.failed_creators if c.get('error')])}")
        
        # Report CSV modifications
        if self.removed_usernames:
            print(f"🗑️ Removed invalid usernames: {len(self.removed_usernames)}")
            print(f"   📄 Invalid usernames saved to: {self.invalid_csv_file}")
            for username in self.removed_usernames:
                print(f"   • @{username} (Bright Data timeout)")
        else:
            print(f"🗑️ No usernames removed from input dataset")
        
        if self.processed_creators:
            print(f"\n🎯 PROCESSED CREATORS:")
            print(f"📊 Use helper functions to generate creator_lookup.csv and creator_post_lookup.csv")
            print(f"💡 Downstream processing will handle engagement/recency filtering")
            
            # Show content database stats
            db_stats = self.content_db.get_stats()
            print(f"\n📚 Content Database Updated:")
            print(f"   Total creators: {db_stats['creator_count']}")
            print(f"   Total posts: {db_stats['total_posts']}")
            print(f"   Database size: {db_stats['db_size_mb']:.1f} MB")
            print(f"   Location: {self.content_db.db_path}")


def run_screening(input_csv_file, verbose=True):
    """
    Main screening runner with enhanced logging and error handling
    
    Args:
        input_csv_file: Path to input CSV file
        verbose: Enable verbose startup logging
    """
    import sys
    import traceback
    
    if verbose:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🚀 Starting Creator Screening Process")
        print(f"⏰ Timestamp: {timestamp}")
        print(f"📂 Input file: {input_csv_file}")
        print(f"📍 Working directory: {os.getcwd()}")
        print("=" * 70)
        sys.stdout.flush()
    
    try:
        # API Keys (should be moved to environment variables in production)
        TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
        BRIGHTDATA_TOKEN = "ddbb0138-fb46-4f00-a9f9-ce085a84dbce"
        
        if verbose:
            print("🔧 Initializing Creator Screener...")
            sys.stdout.flush()
        
        # Initialize screener with hybrid client (TikAPI + Bright Data fallback)
        screener = CreatorScreener(
            TIKAPI_KEY, 
            brightdata_token=BRIGHTDATA_TOKEN
        )
        
        if verbose:
            print("✅ Screener initialized successfully")
            print("🎯 Starting screening process...")
            sys.stdout.flush()
        
        # Check if input file exists
        if not os.path.exists(input_csv_file):
            print(f"❌ Input file not found: {input_csv_file}")
            return False
        
        # Run screening
        screener.screen_all_creators(input_csv_file)
        
        if verbose:
            print("\n🎉 Screening process completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ SCREENING FAILED - Error occurred: {str(e)}")
        print("📋 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    # Default to radar dataset if no argument provided
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/inputs/radar_5k_quitmyjob.csv"
    
    success = run_screening(input_file, verbose=True)
    
    if success:
        print(f"\n✅ Check the data/outputs/ folder for results!")
        sys.exit(0)
    else:
        print(f"\n💥 Screening failed - check logs above for details")
        sys.exit(1)