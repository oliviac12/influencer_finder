#!/usr/bin/env python3
"""
Standalone Email Scheduler for Replit
Pulls from GitHub, sends emails, pushes status back
"""
import subprocess
import time
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def git_pull():
    """Pull latest from GitHub to get new scheduled emails"""
    try:
        subprocess.run(["git", "pull"], check=True, capture_output=True)
        print(f"[{datetime.now().strftime('%I:%M %p')}] Pulled latest from GitHub")
    except Exception as e:
        print(f"Git pull error: {e}")

def git_push():
    """Push updates back to GitHub after sending emails"""
    try:
        subprocess.run(["git", "add", "cache/scheduled_emails.json"], check=True)
        subprocess.run(["git", "commit", "-m", "Update scheduled email status"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"[{datetime.now().strftime('%I:%M %p')}] Pushed status to GitHub")
    except Exception as e:
        # Might fail if no changes, that's ok
        pass

def main():
    print("📧 Standalone Email Scheduler Starting...")
    print("This service only handles sending scheduled emails")
    print("="*50)
    
    from email_scheduler_service import send_email_with_tracking
    from utils.email_scheduler import EmailScheduler
    
    # Initialize scheduler
    scheduler = EmailScheduler(timezone="US/Pacific")
    
    # Start the scheduler with callback
    scheduler.start_background_scheduler(send_email_with_tracking)
    
    print("✅ Scheduler running. Checking every 30 seconds...")
    print("📂 Syncing with GitHub every 5 minutes...")
    
    last_sync = time.time()
    
    while True:
        try:
            # Pull from GitHub every 5 minutes
            if time.time() - last_sync > 300:
                git_pull()
                last_sync = time.time()
            
            # Check for sent emails and push if any
            emails = scheduler.get_emails_to_send_now()
            if emails:
                time.sleep(35)  # Give time to send
                git_push()  # Push status updates
            
            # Show status
            stats = scheduler.get_schedule_stats()
            if stats['pending'] > 0:
                pacific_tz = ZoneInfo("US/Pacific")
                now = datetime.now(pacific_tz)
                print(f"[{now.strftime('%I:%M %p')}] {stats['pending']} pending, {stats['sent']} sent")
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            scheduler.stop_background_scheduler()
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()