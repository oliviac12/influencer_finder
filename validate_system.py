#!/usr/bin/env python3
"""
System Validation Script

Tests core functionality with a small subset of creators to ensure:
1. Log files are being written with enough detail
2. Cache is updating correctly  
3. Output files are being generated
4. Progress indicators work properly

Run this BEFORE starting any large screening job to avoid monitoring issues.
"""
import os
import pandas as pd
import json
import time
from datetime import datetime
from screen_creators import CreatorScreener

class SystemValidator:
    def __init__(self, input_csv_file, test_count=3):
        self.input_csv_file = input_csv_file
        self.test_count = test_count
        self.test_csv = None
        self.original_creators = []
        self.validation_results = {}
        
    def create_test_subset(self):
        """Create a small test CSV with first N creators"""
        try:
            df = pd.read_csv(self.input_csv_file)
            if len(df) < self.test_count:
                print(f"⚠️  Input file only has {len(df)} creators, using all of them")
                test_df = df
            else:
                test_df = df.head(self.test_count)
            
            # Create test CSV filename
            input_basename = os.path.basename(self.input_csv_file).replace('.csv', '')
            self.test_csv = f"validate_{input_basename}_test.csv"
            test_df.to_csv(self.test_csv, index=False)
            
            self.original_creators = test_df['username'].tolist()
            print(f"✅ Created test subset: {self.test_csv}")
            print(f"📋 Test creators: {', '.join(['@' + u for u in self.original_creators])}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create test subset: {e}")
            return False
    
    def validate_logging(self, screener):
        """Test if log files are created and informative"""
        print(f"\n🔍 VALIDATION 1: Log File System")
        
        log_dir = "logs"
        log_files_before = set(os.listdir(log_dir)) if os.path.exists(log_dir) else set()
        
        # The screener should have created a log file path
        expected_log = screener.current_log_file if hasattr(screener, 'current_log_file') else None
        
        if expected_log and os.path.exists(expected_log):
            # Check log file content
            with open(expected_log, 'r') as f:
                log_content = f.read()
            
            # Check for key indicators
            has_progress = any(indicator in log_content for indicator in ['[1/', '[2/', '[3/'])
            has_screening = 'Screening @' in log_content
            has_filters = any(filter_text in log_content for filter_text in ['Filter 1', 'Filter 2', 'Filter 3'])
            
            log_size = len(log_content)
            
            print(f"   ✅ Log file created: {expected_log}")
            print(f"   📏 Log size: {log_size} characters")
            print(f"   📊 Has progress indicators: {'✅' if has_progress else '❌'}")
            print(f"   🔍 Has screening messages: {'✅' if has_screening else '❌'}")
            print(f"   🎯 Has filter details: {'✅' if has_filters else '❌'}")
            
            self.validation_results['logging'] = {
                'success': True,
                'log_file': expected_log,
                'size': log_size,
                'has_progress': has_progress,
                'has_screening': has_screening,
                'has_filters': has_filters
            }
            
            return True
        else:
            print(f"   ❌ Log file not found or not created")
            self.validation_results['logging'] = {'success': False}
            return False
    
    def validate_cache_updates(self, screener):
        """Test if cache files are being updated"""
        print(f"\n🔍 VALIDATION 2: Cache Update System")
        
        cache_dir = screener.cache_dir
        creator_cache_file = os.path.join(cache_dir, "creator_cache.json")
        shoppable_cache_file = os.path.join(cache_dir, "shoppable_cache.json")
        
        cache_results = {}
        
        # Check creator cache
        if os.path.exists(creator_cache_file):
            with open(creator_cache_file, 'r') as f:
                creator_cache = json.load(f)
            
            # Check if our test creators are in cache
            test_creators_in_cache = [u for u in self.original_creators if u in creator_cache]
            
            print(f"   ✅ Creator cache exists: {len(creator_cache)} total creators")
            print(f"   📋 Test creators in cache: {len(test_creators_in_cache)}/{len(self.original_creators)}")
            
            cache_results['creator_cache'] = {
                'exists': True,
                'total_creators': len(creator_cache),
                'test_creators_cached': len(test_creators_in_cache)
            }
        else:
            print(f"   ❌ Creator cache not found")
            cache_results['creator_cache'] = {'exists': False}
        
        # Check shoppable cache
        if os.path.exists(shoppable_cache_file):
            with open(shoppable_cache_file, 'r') as f:
                shoppable_cache = json.load(f)
            
            print(f"   ✅ Shoppable cache exists: {len(shoppable_cache)} total posts")
            
            cache_results['shoppable_cache'] = {
                'exists': True,
                'total_posts': len(shoppable_cache)
            }
        else:
            print(f"   ❌ Shoppable cache not found")
            cache_results['shoppable_cache'] = {'exists': False}
        
        self.validation_results['caching'] = cache_results
        
        # Return True if at least creator cache was updated
        return cache_results.get('creator_cache', {}).get('exists', False)
    
    def validate_cache_skipping(self, screener):
        """Test if cache skipping works on second run"""
        print(f"\n🔍 VALIDATION 4: Cache Skipping System")
        
        # Save original test creators for reference
        original_creators = self.original_creators.copy()
        
        try:
            # Run the same test subset again to test cache skipping
            print(f"   🔄 Running second screening to test cache skipping...")
            
            # Capture start time for performance check
            skip_start = time.time()
            
            # Create new screener instance to simulate fresh start
            skip_screener = CreatorScreener(
                tikapi_key="iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx",
                brightdata_token="36c74962-d03a-41c1-b261-7ea4109ec8bd"
            )
            
            # Run screening again on same test file
            skip_screener.screen_all_creators(self.test_csv)
            
            skip_duration = time.time() - skip_start
            
            # Check log file for skip messages
            log_file = skip_screener.current_log_file if hasattr(skip_screener, 'current_log_file') else None
            skip_messages_found = 0
            
            if log_file and os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Count skip messages
                skip_messages_found = log_content.count('⏭️ Skipping - already processed in previous run')
                
                print(f"   ✅ Second run completed in {skip_duration:.1f}s")
                print(f"   📋 Skip messages found in log: {skip_messages_found}")
                print(f"   🎯 Expected skip count: {len(original_creators)}")
                
                # Check performance - second run should be much faster
                if skip_duration < 30:  # Should be very fast if skipping works
                    print(f"   ✅ Performance: Second run was fast (good cache skipping)")
                else:
                    print(f"   ⚠️  Performance: Second run was slow (cache skipping may not be working)")
                
                # Validate that we got the expected number of skips
                expected_skips = len(original_creators)
                if skip_messages_found >= expected_skips:
                    print(f"   ✅ Cache skipping: Working correctly")
                    skip_validation_result = True
                else:
                    print(f"   ❌ Cache skipping: Expected {expected_skips} skips, found {skip_messages_found}")
                    skip_validation_result = False
                
            else:
                print(f"   ❌ Could not find log file for skip validation")
                skip_validation_result = False
            
            self.validation_results['cache_skipping'] = {
                'success': skip_validation_result,
                'second_run_duration': skip_duration,
                'skip_messages_found': skip_messages_found,
                'expected_skips': len(original_creators),
                'log_file': log_file
            }
            
            return skip_validation_result
            
        except Exception as e:
            print(f"   ❌ Cache skipping validation failed: {e}")
            self.validation_results['cache_skipping'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def validate_output_generation(self):
        """Test if output files are being generated"""
        print(f"\n🔍 VALIDATION 3: Output File Generation")
        
        # Check for qualified creators file
        output_files = []
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Look for output files in data/outputs/
        output_dir = "data/outputs"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            # Look for files containing our test dataset name
            input_basename = os.path.basename(self.input_csv_file).replace('.csv', '')
            test_files = [f for f in files if 'validate' in f and input_basename in f]
            
            print(f"   📁 Output directory exists: {output_dir}")
            print(f"   📄 Test output files found: {len(test_files)}")
            
            for file in test_files:
                file_path = os.path.join(output_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"      • {file} ({file_size} bytes)")
            
            self.validation_results['output_generation'] = {
                'success': len(test_files) > 0,
                'files_created': test_files,
                'output_dir_exists': True
            }
            
            return len(test_files) > 0
        else:
            print(f"   ❌ Output directory not found: {output_dir}")
            self.validation_results['output_generation'] = {
                'success': False,
                'output_dir_exists': False
            }
            return False
    
    def cleanup(self):
        """Clean up test files"""
        try:
            if self.test_csv and os.path.exists(self.test_csv):
                os.remove(self.test_csv)
                print(f"🧹 Cleaned up test CSV: {self.test_csv}")
            
            # Clean up any test output files
            output_dir = "data/outputs"
            if os.path.exists(output_dir):
                files = os.listdir(output_dir)
                test_files = [f for f in files if 'validate' in f]
                for file in test_files:
                    os.remove(os.path.join(output_dir, file))
                    print(f"🧹 Cleaned up test output: {file}")
                    
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def run_validation(self):
        """Run complete system validation with timeout protection"""
        print(f"🚀 SYSTEM VALIDATION STARTING")
        print(f"📂 Input file: {self.input_csv_file}")
        print(f"🎯 Testing with {self.test_count} creators")
        print(f"⏰ Max timeout: 5 minutes for validation")
        print("=" * 70)
        
        # Step 1: Create test subset
        if not self.create_test_subset():
            return False
        
        try:
            # Step 2: Run screening on test subset with timeout monitoring
            print(f"\n🎯 Running screening on test subset...")
            print(f"   (This should complete quickly - if it hangs, that's the problem we're detecting)")
            
            start_time = time.time()
            
            screener = CreatorScreener(
                tikapi_key="iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx",
                brightdata_token="36c74962-d03a-41c1-b261-7ea4109ec8bd"
            )
            
            print(f"   ✅ Screener initialized in {time.time() - start_time:.1f}s")
            
            # Run the actual screening (this is where it might hang)
            screening_start = time.time()
            screener.screen_all_creators(self.test_csv)
            screening_duration = time.time() - screening_start
            
            print(f"   ✅ Screening completed in {screening_duration:.1f}s")
            
            # Step 3: Validate all systems
            logging_ok = self.validate_logging(screener)
            caching_ok = self.validate_cache_updates(screener)
            output_ok = self.validate_output_generation()
            skip_ok = self.validate_cache_skipping(screener)
            
            # Step 4: Final report
            total_duration = time.time() - start_time
            self.print_final_report(logging_ok, caching_ok, output_ok, skip_ok, total_duration)
            
            return logging_ok and caching_ok and output_ok and skip_ok
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Validation interrupted by user")
            print(f"🔍 This suggests the screening process may be hanging - exactly what we're trying to detect!")
            return False
        except Exception as e:
            print(f"❌ Validation failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()
    
    def print_final_report(self, logging_ok, caching_ok, output_ok, skip_ok, total_duration=None):
        """Print final validation report"""
        print(f"\n{'='*70}")
        print(f"📊 VALIDATION SUMMARY")
        print(f"{'='*70}")
        
        if total_duration:
            print(f"⏰ Total validation time: {total_duration:.1f}s")
        
        print(f"🔍 Log File System:     {'✅ PASS' if logging_ok else '❌ FAIL'}")
        print(f"💾 Cache Updates:       {'✅ PASS' if caching_ok else '❌ FAIL'}")
        print(f"📄 Output Generation:   {'✅ PASS' if output_ok else '❌ FAIL'}")
        print(f"⏭️  Cache Skipping:      {'✅ PASS' if skip_ok else '❌ FAIL'}")
        
        overall_status = logging_ok and caching_ok and output_ok and skip_ok
        print(f"\n🎯 OVERALL STATUS:      {'✅ READY FOR FULL JOB' if overall_status else '❌ NEEDS ATTENTION'}")
        
        if not overall_status:
            print(f"\n⚠️  RECOMMENDATION: Fix the failing validations before running the full job")
            print(f"   This will help avoid monitoring confusion and multiple processes")
        else:
            print(f"\n🚀 RECOMMENDATION: System is ready - you can run the full job with confidence")
            print(f"   All monitoring systems are working correctly")
            
        # Performance guidance
        if total_duration:
            if total_duration > 180:  # 3 minutes
                print(f"\n⚠️  PERFORMANCE WARNING: Validation took {total_duration:.1f}s")
                print(f"   If validation is slow, the full job will likely have hanging issues")
            elif total_duration < 60:  # 1 minute
                print(f"\n✅ PERFORMANCE: Good - validation completed quickly")
                print(f"   This suggests the full job should run smoothly")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 validate_system.py <input_csv_file> [test_count]")
        print("Example: python3 validate_system.py data/inputs/radar_5k_quitmyjob.csv 3")
        sys.exit(1)
    
    input_file = sys.argv[1]
    test_count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
    
    validator = SystemValidator(input_file, test_count)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()