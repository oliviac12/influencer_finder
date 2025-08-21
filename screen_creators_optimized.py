"""
Optimized Bulk Creator Data Collection
High-performance screening with thread-safe caching and smart batching
"""
import pandas as pd
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
from queue import Queue
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Tuple


class ThreadSafeCache:
    """Thread-safe cache implementation"""
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    
    def get(self, key, default=None):
        with self._lock:
            return self._cache.get(key, default)
    
    def set(self, key, value):
        with self._lock:
            self._cache[key] = value
    
    def update(self, items):
        with self._lock:
            self._cache.update(items)
    
    def keys(self):
        with self._lock:
            return list(self._cache.keys())
    
    def to_dict(self):
        with self._lock:
            return self._cache.copy()
    
    def from_dict(self, data):
        with self._lock:
            self._cache = data.copy()
    
    def __len__(self):
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, key):
        with self._lock:
            return key in self._cache


class AdaptiveRateLimiter:
    """Adaptive rate limiting based on API responses"""
    def __init__(self, initial_delay=1.0):
        self.delay = initial_delay
        self.min_delay = 0.3
        self.max_delay = 5.0
        self._lock = threading.Lock()
        self.success_count = 0
        self.error_count = 0
    
    def wait(self):
        """Wait with current delay"""
        with self._lock:
            current_delay = self.delay
        time.sleep(current_delay)
    
    def success(self):
        """Speed up on success"""
        with self._lock:
            self.success_count += 1
            if self.success_count > 5:  # Speed up after 5 successes
                self.delay = max(self.min_delay, self.delay * 0.9)
                self.success_count = 0
    
    def error(self):
        """Slow down on error"""
        with self._lock:
            self.error_count += 1
            self.delay = min(self.max_delay, self.delay * 1.5)
    
    def rate_limited(self):
        """Significantly slow down on rate limit"""
        with self._lock:
            self.delay = min(self.max_delay, self.delay * 2)
            self.error_count = 0


class OptimizedCreatorScreener:
    def __init__(self, tikapi_key, brightdata_token=None, max_workers=3):
        # API clients
        if brightdata_token:
            self.data_client = CreatorDataClient(tikapi_key, brightdata_token)
            print("🔄 Using hybrid client: TikAPI + Bright Data MCP fallback")
        else:
            self.data_client = TikAPIClient(tikapi_key)
            print("🔥 Using TikAPI client only")
        
        # Initialize optimized shoppable filter with session pooling
        self.shoppable_filter = ShoppableContentFilter()
        self._setup_http_session()
        
        # Initialize content database for automatic saving
        self.content_db = ContentDatabase()
        
        # Thread-safe caches
        self.creator_cache = ThreadSafeCache()
        self.shoppable_cache = ThreadSafeCache()
        self.invalid_usernames = set()
        self.existing_creators = set()
        
        # Rate limiting
        self.rate_limiter = AdaptiveRateLimiter()
        
        # Thread pool settings
        self.max_workers = max_workers
        
        # Results storage
        self.processed_creators = []
        self.failed_creators = []
        self.creator_lookup_data = []
        self.creator_post_lookup_data = []
        
        # Locks for thread safety
        self._results_lock = threading.Lock()
        self._print_lock = threading.Lock()
        
        # Cache directory (will be set per dataset)
        self.cache_dir = None
        self.input_csv_file = None
        self.removed_usernames = []
    
    def _setup_http_session(self):
        """Setup HTTP session with connection pooling and retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Update shoppable filter to use pooled session
        self.shoppable_filter.session = session
    
    def screen_all_creators(self, csv_file="data/inputs/radar_5k_quitmyjob.csv", output_file=None):
        """Screen all creators with optimized parallel processing"""
        
        # Setup paths and caching
        input_basename = os.path.basename(csv_file).replace('.csv', '')
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        self.cache_dir = f"cache/screening/{input_basename}_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.input_csv_file = csv_file
        
        # Load caches
        self._load_all_caches()
        
        print(f"🚀 OPTIMIZED Creator Screening")
        print(f"📁 Input: {csv_file}")
        print(f"🔧 Settings: {self.max_workers} workers, adaptive rate limiting")
        print(f"📋 Cache: {len(self.creator_cache)} creators, {len(self.shoppable_cache)} posts cached")
        print("=" * 70)
        
        # Read creator data
        try:
            df = pd.read_csv(csv_file)
            creators = df.to_dict('records')
            print(f"📊 Loading {len(creators)} creators from {csv_file}")
        except Exception as e:
            print(f"❌ Error reading {csv_file}: {e}")
            return
        
        # Filter creators to process
        creators_to_process = self._filter_creators_to_process(creators)
        
        if not creators_to_process:
            print("✅ All creators already processed!")
            return
        
        print(f"🎯 Processing {len(creators_to_process)} new creators")
        
        # Process in optimized batches
        self._process_creators_optimized(creators_to_process)
        
        # Save results
        self.save_dataframes()
        self._save_all_caches()
        self.print_summary()
    
    def _filter_creators_to_process(self, creators):
        """Filter out already processed and invalid creators"""
        to_process = []
        
        for i, creator in enumerate(creators, 1):
            username = creator['username']
            
            if username in self.existing_creators:
                print(f"[{i}/{len(creators)}] ⏭️ @{username} - already cached")
                continue
            
            if username in self.invalid_usernames:
                print(f"[{i}/{len(creators)}] 🚫 @{username} - invalid username")
                continue
            
            to_process.append(creator)
        
        return to_process
    
    def _process_creators_optimized(self, creators):
        """Process creators with optimized batching and parallel execution"""
        
        # Process in chunks for better memory management
        chunk_size = 50
        total_processed = 0
        
        for chunk_start in range(0, len(creators), chunk_size):
            chunk = creators[chunk_start:chunk_start + chunk_size]
            chunk_num = (chunk_start // chunk_size) + 1
            total_chunks = (len(creators) + chunk_size - 1) // chunk_size
            
            print(f"\n📦 Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} creators)")
            
            # Step 1: Fetch creator data in parallel
            creator_data = self._fetch_creator_data_parallel(chunk)
            
            # Step 2: Collect all URLs that need checking
            urls_to_check = self._collect_urls_to_check(creator_data)
            
            if urls_to_check:
                print(f"🔍 Batch checking {len(urls_to_check)} URLs for shoppable content...")
                
                # Step 3: Batch check all URLs at once
                shoppable_results = self._batch_check_shoppable_urls(urls_to_check)
                
                # Update cache
                self.shoppable_cache.update(shoppable_results)
            
            # Step 4: Process results and update records
            self._process_chunk_results(creator_data)
            
            total_processed += len(chunk)
            print(f"✅ Chunk complete: {total_processed}/{len(creators)} creators processed")
            
            # Save caches after each chunk
            self._save_all_caches()
    
    def _fetch_creator_data_parallel(self, creators):
        """Fetch creator data in parallel with rate limiting"""
        creator_data = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_creator = {
                executor.submit(self._fetch_single_creator, creator): creator
                for creator in creators
            }
            
            # Process completed tasks
            for future in as_completed(future_to_creator):
                creator = future_to_creator[future]
                
                try:
                    result = future.result()
                    if result:
                        creator_data.append(result)
                        self.rate_limiter.success()
                except Exception as e:
                    with self._print_lock:
                        print(f"❌ Error fetching @{creator['username']}: {e}")
                    self.rate_limiter.error()
        
        return creator_data
    
    def _fetch_single_creator(self, creator_info):
        """Fetch data for a single creator with caching"""
        username = creator_info['username']
        
        # Check cache first
        cached = self.creator_cache.get(username)
        if cached:
            with self._print_lock:
                print(f"📋 @{username} - using cached data")
            return {
                'username': username,
                'creator_info': creator_info,
                'api_result': cached,
                'from_cache': True
            }
        
        # Rate limit before API call
        self.rate_limiter.wait()
        
        with self._print_lock:
            print(f"🔄 @{username} - fetching from API...")
        
        # Fetch from API
        result = self.data_client.get_creator_analysis(username, post_count=35)
        
        if result['success']:
            # Cache successful result
            self.creator_cache.set(username, result)
            
            return {
                'username': username,
                'creator_info': creator_info,
                'api_result': result,
                'from_cache': False
            }
        else:
            # Handle errors
            error_msg = result.get('error', '').lower()
            
            if 'rate' in error_msg:
                self.rate_limiter.rate_limited()
                with self._print_lock:
                    print(f"⚠️ Rate limited on @{username}")
            
            if any(phrase in error_msg for phrase in ['user not found', 'doesn\'t exist', 'invalid']):
                self.invalid_usernames.add(username)
            
            return None
    
    def _collect_urls_to_check(self, creator_data_list):
        """Collect all URLs that need shoppable checking"""
        urls_to_check = []
        
        for data in creator_data_list:
            if not data or not data['api_result']['success']:
                continue
            
            posts = data['api_result']['posts']
            
            # Get recent video posts
            video_posts = [p for p in posts if not p.get('is_photo_post', False)][:28]
            
            for post in video_posts:
                url = post.get('tiktok_url')
                if url and url not in self.shoppable_cache:
                    urls_to_check.append(url)
        
        return urls_to_check
    
    def _batch_check_shoppable_urls(self, urls):
        """Efficiently batch check URLs for shoppable content"""
        results = {}
        
        # Process in batches of 10
        batch_size = 10
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            
            with self._print_lock:
                print(f"  Checking batch {i//batch_size + 1}/{(len(urls) + batch_size - 1)//batch_size}")
            
            try:
                batch_results = self.shoppable_filter.check_batch_tiktok_commission_eligible(batch)
                results.update(batch_results)
                
                # Log if we found shoppable content
                shoppable_count = sum(1 for v in batch_results.values() if v)
                if shoppable_count > 0:
                    with self._print_lock:
                        print(f"  ✅ Found {shoppable_count} shoppable posts in batch")
                
            except Exception as e:
                with self._print_lock:
                    print(f"  ❌ Batch check failed: {e}")
                # Mark all as non-shoppable on error
                for url in batch:
                    results[url] = False
        
        return results
    
    def _process_chunk_results(self, creator_data_list):
        """Process results for a chunk of creators"""
        
        for data in creator_data_list:
            if not data or not data['api_result']['success']:
                continue
            
            username = data['username']
            creator_info = data['creator_info']
            api_result = data['api_result']
            profile = api_result['profile']
            posts = api_result['posts']
            
            # Process posts and check for shoppable content
            video_posts = [p for p in posts if not p.get('is_photo_post', False)][:28]
            shoppable_posts = []
            
            # Collect creator profile data
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
            
            with self._results_lock:
                self.creator_lookup_data.append(creator_lookup_row)
            
            # Check shoppable status for each post
            for post in video_posts[:10]:  # Check first 10 posts
                url = post.get('tiktok_url')
                if not url:
                    continue
                
                is_shoppable = self.shoppable_cache.get(url, False)
                
                # Collect post data
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
                
                with self._results_lock:
                    self.creator_post_lookup_data.append(post_lookup_row)
                
                if is_shoppable:
                    shoppable_posts.append(post)
            
            # Calculate metrics
            avg_views = self._calculate_average_views(video_posts[:5]) if video_posts else 0
            
            # Determine qualification
            qualified = len(shoppable_posts) > 0
            
            # Create result
            result = {
                'username': username,
                'nickname': profile['nickname'],
                'followers': profile['followers'],
                'total_posts_analyzed': len(video_posts),
                'video_posts_found': len(video_posts),
                'photo_posts_filtered': len(posts) - len(video_posts),
                'shoppable_posts_found': len(shoppable_posts),
                'avg_views': avg_views,
                'qualified': qualified,
                'error': None,
                'failure_reason': "No shoppable content found" if not qualified else None,
                'original_data': creator_info
            }
            
            # Save to content database if qualified
            if qualified and len(shoppable_posts) > 0:
                try:
                    # Prepare posts data for content database
                    posts_for_db = []
                    for post in video_posts[:30]:  # Save up to 30 posts
                        post_data = {
                            'id': post.get('id', ''),
                            'desc': post.get('description', ''),
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
                            'tags': post.get('hashtags', [])  # Include hashtags if available
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
                except Exception as e:
                    with self._print_lock:
                        print(f"   ⚠️ Warning: Could not save @{username} to content database: {e}")
            
            # Add to results
            with self._results_lock:
                if qualified:
                    self.processed_creators.append(result)
                    with self._print_lock:
                        print(f"✅ @{username} QUALIFIED - {len(shoppable_posts)} shoppable, {avg_views:,} avg views")
                else:
                    self.failed_creators.append(result)
                    with self._print_lock:
                        print(f"❌ @{username} - No shoppable content")
    
    def _calculate_average_views(self, posts):
        """Calculate average views for posts"""
        if not posts:
            return 0
        total_views = sum(post.get('stats', {}).get('views', 0) for post in posts)
        return total_views // len(posts)
    
    def _load_all_caches(self):
        """Load all caches from disk"""
        # Load creator cache
        creator_cache_file = os.path.join(self.cache_dir, "creator_cache.json")
        if os.path.exists(creator_cache_file):
            with open(creator_cache_file, 'r') as f:
                data = json.load(f)
                self.creator_cache.from_dict(data)
                self.existing_creators = set(data.keys())
        
        # Load shoppable cache
        shoppable_cache_file = os.path.join(self.cache_dir, "shoppable_cache.json")
        if os.path.exists(shoppable_cache_file):
            with open(shoppable_cache_file, 'r') as f:
                data = json.load(f)
                self.shoppable_cache.from_dict(data)
        
        # Load invalid usernames
        invalid_file = os.path.join(self.cache_dir, "invalid_usernames.json")
        if os.path.exists(invalid_file):
            with open(invalid_file, 'r') as f:
                self.invalid_usernames = set(json.load(f))
    
    def _save_all_caches(self):
        """Save all caches to disk"""
        try:
            # Save creator cache
            with open(os.path.join(self.cache_dir, "creator_cache.json"), 'w') as f:
                json.dump(self.creator_cache.to_dict(), f, indent=2)
            
            # Save shoppable cache
            with open(os.path.join(self.cache_dir, "shoppable_cache.json"), 'w') as f:
                json.dump(self.shoppable_cache.to_dict(), f, indent=2)
            
            # Save invalid usernames
            with open(os.path.join(self.cache_dir, "invalid_usernames.json"), 'w') as f:
                json.dump(list(self.invalid_usernames), f, indent=2)
            
            print(f"💾 Caches saved: {len(self.creator_cache)} creators, {len(self.shoppable_cache)} posts")
        except Exception as e:
            print(f"❌ Error saving caches: {e}")
    
    def save_dataframes(self):
        """Save creator and post data to CSV files"""
        try:
            # Save creator lookup data
            if self.creator_lookup_data:
                new_df = pd.DataFrame(self.creator_lookup_data)
                
                if os.path.exists('creator_lookup.csv'):
                    existing_df = pd.read_csv('creator_lookup.csv')
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['username'], keep='last')
                else:
                    combined_df = new_df
                
                combined_df.to_csv('creator_lookup.csv', index=False)
                print(f"💾 Saved {len(combined_df)} creators to creator_lookup.csv")
            
            # Save post lookup data
            if self.creator_post_lookup_data:
                new_df = pd.DataFrame(self.creator_post_lookup_data)
                
                if os.path.exists('creator_post_lookup.csv'):
                    existing_df = pd.read_csv('creator_post_lookup.csv')
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['url'], keep='last')
                else:
                    combined_df = new_df
                
                combined_df.to_csv('creator_post_lookup.csv', index=False)
                print(f"💾 Saved {len(combined_df)} posts to creator_post_lookup.csv")
                
        except Exception as e:
            print(f"❌ Error saving dataframes: {e}")
    
    def print_summary(self):
        """Print processing summary"""
        total = len(self.processed_creators) + len(self.failed_creators)
        
        print(f"\n{'='*60}")
        print(f"📊 SCREENING SUMMARY")
        print(f"{'='*60}")
        print(f"Total creators screened: {total}")
        print(f"✅ Qualified (with shoppable): {len(self.processed_creators)}")
        print(f"❌ No shoppable content: {len([c for c in self.failed_creators if not c.get('error')])}")
        print(f"🔥 API errors: {len([c for c in self.failed_creators if c.get('error')])}")
        print(f"\n🎯 Performance Stats:")
        print(f"  • Cache hit rate: {len(self.existing_creators)}/{total + len(self.existing_creators)} creators")
        print(f"  • Shoppable cache: {len(self.shoppable_cache)} posts cached")
        print(f"  • Rate limiter delay: {self.rate_limiter.delay:.2f}s")
        
        # Show content database stats
        if self.processed_creators:
            db_stats = self.content_db.get_stats()
            print(f"\n📚 Content Database Updated:")
            print(f"  • Total creators: {db_stats['creator_count']}")
            print(f"  • Total posts: {db_stats['total_posts']}")
            print(f"  • Database size: {db_stats['db_size_mb']:.1f} MB")
            print(f"  • Location: {self.content_db.db_path}")


def run_optimized_screening(input_csv_file, max_workers=3):
    """Run optimized screening with all improvements"""
    import sys
    import traceback
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 Starting OPTIMIZED Creator Screening")
    print(f"⏰ Timestamp: {timestamp}")
    print(f"📂 Input file: {input_csv_file}")
    print(f"🔧 Workers: {max_workers}")
    print("=" * 70)
    
    try:
        # API Keys
        TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
        BRIGHTDATA_TOKEN = "36c74962-d03a-41c1-b261-7ea4109ec8bd"
        
        # Initialize optimized screener
        screener = OptimizedCreatorScreener(
            TIKAPI_KEY,
            brightdata_token=BRIGHTDATA_TOKEN,
            max_workers=max_workers
        )
        
        # Check if input file exists
        if not os.path.exists(input_csv_file):
            print(f"❌ Input file not found: {input_csv_file}")
            return False
        
        # Run screening
        screener.screen_all_creators(input_csv_file)
        
        print("\n🎉 Screening completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ SCREENING FAILED: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    # Default input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = "data/inputs/radar_5k_quitmyjob.csv"
    
    # Optional: specify number of workers
    max_workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    success = run_optimized_screening(input_file, max_workers)
    
    if success:
        print(f"\n✅ Check the data/outputs/ folder for results!")
        sys.exit(0)
    else:
        print(f"\n💥 Screening failed - check logs above")
        sys.exit(1)