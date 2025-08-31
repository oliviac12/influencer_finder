"""
Backfill Retry Script - Find and Process Missing Creators
This script identifies creators that exist in CSV files but are missing from the content database
and retries processing them with better error handling and logging.
"""
import pandas as pd
import json
import os
import time
from datetime import datetime
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backfill.backfill_content_data import ContentBackfiller
from utils.content_database import ContentDatabase


class MissingCreatorBackfiller:
    def __init__(self, tikapi_key, brightdata_token):
        self.tikapi_key = tikapi_key
        self.brightdata_token = brightdata_token
        self.content_db = ContentDatabase()
        self.backfiller = ContentBackfiller(tikapi_key, brightdata_token)
        
        # Setup logging
        log_filename = f"logs/missing_creators_backfill_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Track failures for retry
        self.failed_creators = {}
        self.max_retries = 3
    
    def find_missing_creators(self):
        """Find all creators in CSV files that are missing from the database"""
        # Get all creators from CSV files
        csv_creators = self._get_all_csv_creators()
        
        # Get all creators currently in database
        db = self.content_db.load_database()
        db_creators = set(db.get('creators', {}).keys())
        
        # Load invalid creators from the screening-level file
        invalid_creators = set()
        invalid_file = "cache/screening/invalid_usernames.json"
        if os.path.exists(invalid_file):
            try:
                with open(invalid_file, 'r') as f:
                    invalid_list = json.load(f)
                    invalid_creators = set(invalid_list)
                    self.logger.info(f"📄 Loaded {len(invalid_creators)} invalid creators from master list")
            except Exception as e:
                self.logger.warning(f"Could not load {invalid_file}: {e}")
        
        # Find missing creators (excluding those already marked invalid)
        missing_creators = csv_creators - db_creators - invalid_creators
        
        self.logger.info(f"📊 Total creators in CSVs: {len(csv_creators)}")
        self.logger.info(f"📊 Total creators in database: {len(db_creators)}")
        self.logger.info(f"❌ Already marked invalid: {len(invalid_creators)}")
        self.logger.info(f"❓ Missing creators to process: {len(missing_creators)}")
        
        return list(missing_creators)
    
    def _get_all_csv_creators(self):
        """Get all unique creator usernames from CSV files"""
        all_creators = set()
        input_dir = "data/inputs/"
        
        for filename in os.listdir(input_dir):
            if filename.endswith('.csv'):
                csv_path = os.path.join(input_dir, filename)
                try:
                    df = pd.read_csv(csv_path)
                    username_cols = [col for col in df.columns if 'username' in col.lower()]
                    if username_cols:
                        usernames = df[username_cols[0]].dropna().unique()
                        all_creators.update(usernames)
                        self.logger.info(f"📁 {filename}: {len(usernames)} creators")
                except Exception as e:
                    self.logger.error(f"Error reading {filename}: {e}")
        
        return all_creators
    
    def retry_missing_creators(self, missing_creators):
        """Process missing creators with retry logic"""
        self.logger.info(f"\n🔄 Starting to process {len(missing_creators)} missing creators...")
        
        success_count = 0
        permanent_fail_count = 0
        
        for i, username in enumerate(missing_creators, 1):
            self.logger.info(f"\n[{i}/{len(missing_creators)}] Processing @{username}")
            
            retry_count = 0
            success = False
            
            while retry_count < self.max_retries and not success:
                try:
                    # Try to extract content
                    data, error = self.backfiller.extract_content_brightdata(username)
                    
                    if data is not None:
                        # Save to database
                        profile_data, top_posts_data = data
                        
                        if top_posts_data:
                            self.content_db.save_creator_content(username, profile_data, top_posts_data)
                            self.logger.info(f"   ✅ Saved @{username}: {len(top_posts_data)} posts")
                            success = True
                            success_count += 1
                        else:
                            self.logger.warning(f"   ⚠️  No posts data for @{username}")
                            break  # Don't retry if no posts
                    else:
                        self.logger.warning(f"   ❌ Attempt {retry_count + 1} failed: {error}")
                        
                        # Check if error is retryable
                        if "Building snapshot" in error:
                            self.logger.info("   ⏳ Waiting 30s for snapshot to build...")
                            time.sleep(30)
                        elif "timeout" in error.lower():
                            self.logger.info("   ⏳ Timeout error, waiting 10s before retry...")
                            time.sleep(10)
                        else:
                            # Non-retryable error
                            break
                    
                except Exception as e:
                    self.logger.error(f"   💥 Unexpected error: {e}")
                
                retry_count += 1
                if not success and retry_count < self.max_retries:
                    time.sleep(2)  # Brief pause between retries
            
            if not success:
                self.failed_creators[username] = f"Failed after {retry_count} attempts"
                permanent_fail_count += 1
                self.logger.error(f"   ❌ PERMANENTLY FAILED: @{username}")
            
            # Progress update every creator
            progress_pct = i/len(missing_creators)*100
            self.logger.info(f"\n📊 PROGRESS: {i}/{len(missing_creators)} ({progress_pct:.1f}%) - Success: {success_count} | Failed: {permanent_fail_count}")
        
        return success_count, permanent_fail_count
    
    def save_failed_creators_report(self):
        """Save a report of creators that permanently failed"""
        if self.failed_creators:
            # Save detailed report with timestamps
            report_file = f"failed_creators_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(self.failed_creators, f, indent=2)
            self.logger.info(f"\n📄 Failed creators report saved to: {report_file}")
            
            # Also save to the screening-level invalid_usernames.json file
            invalid_file = "cache/screening/invalid_usernames.json"
            existing_invalid = []
            
            # Load existing if file exists
            if os.path.exists(invalid_file):
                try:
                    with open(invalid_file, 'r') as f:
                        existing_invalid = json.load(f)
                except:
                    existing_invalid = []
            
            # Convert to set to avoid duplicates
            invalid_set = set(existing_invalid)
            invalid_set.update(self.failed_creators.keys())
            
            # Save updated list as JSON array
            with open(invalid_file, 'w') as f:
                json.dump(sorted(list(invalid_set)), f, indent=2)
            
            self.logger.info(f"📄 Invalid creators list updated: {invalid_file} ({len(invalid_set)} total)")
    
    def run(self):
        """Main execution"""
        self.logger.info("🚀 Missing Creator Backfill Script Starting...")
        self.logger.info("=" * 60)
        
        # Find missing creators
        missing_creators = self.find_missing_creators()
        
        if not missing_creators:
            self.logger.info("✅ No missing creators found! Database is complete.")
            return
        
        # Show some examples
        self.logger.info(f"\n📋 Sample missing creators:")
        for creator in missing_creators[:10]:
            self.logger.info(f"   - @{creator}")
        if len(missing_creators) > 10:
            self.logger.info(f"   ... and {len(missing_creators) - 10} more")
        
        # Check if astoldbyanisa is in the list
        if 'astoldbyanisa' in missing_creators:
            self.logger.info("\n🎯 Found 'astoldbyanisa' in missing creators list!")
        
        # Process missing creators
        success_count, fail_count = self.retry_missing_creators(missing_creators)
        
        # Final summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 FINAL SUMMARY")
        self.logger.info(f"   Total missing creators: {len(missing_creators)}")
        self.logger.info(f"   ✅ Successfully processed: {success_count}")
        self.logger.info(f"   ❌ Permanently failed: {fail_count}")
        
        # Save failed creators report
        self.save_failed_creators_report()
        
        # Check database stats
        stats = self.content_db.get_stats()
        self.logger.info(f"\n📊 Database now contains:")
        self.logger.info(f"   Creators: {stats['creator_count']}")
        self.logger.info(f"   Total posts: {stats['total_posts']}")


if __name__ == "__main__":
    # API keys
    TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
    BRIGHTDATA_TOKEN = "ddbb0138-fb46-4f00-a9f9-ce085a84dbce"
    
    # Run the missing creator backfill
    backfiller = MissingCreatorBackfiller(TIKAPI_KEY, BRIGHTDATA_TOKEN)
    backfiller.run()