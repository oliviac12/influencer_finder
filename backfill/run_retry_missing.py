#!/usr/bin/env python3
"""
Run Missing Creators Retry as Background Job
Simple wrapper to run the retry script in background with progress monitoring
"""
import subprocess
import os
import sys
from datetime import datetime

def main():
    print("🚀 Starting Missing Creators Retry Job...")
    print("📊 This will process ~93 missing creators with 3 retry attempts each")
    print("⏱️  Estimated time: 30-60 minutes")
    print(f"📋 Log file: logs/missing_creators_backfill_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    print("="*60)
    
    # Run the backfill retry script
    script_path = os.path.join(os.path.dirname(__file__), "backfill_retry_missing.py")
    
    try:
        # Start the process
        subprocess.run([sys.executable, script_path])
    except KeyboardInterrupt:
        print("\n⏹️  Process stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()