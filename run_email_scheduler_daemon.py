#!/usr/bin/env python3
"""
Email Scheduler Daemon
Run this in the background to continuously process scheduled emails
Usage: python3 run_email_scheduler_daemon.py
"""
import sys
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_scheduler import EmailScheduler
from app.email_outreach_v2 import EmailOutreachManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("📧 Email Scheduler Daemon Starting...")
    print("Press Ctrl+C to stop\n")
    
    # Initialize components
    scheduler = EmailScheduler(timezone="US/Pacific")
    email_manager = EmailOutreachManager()
    
    # Define email sending callback
    def send_email_callback(to_email, subject, body, username=None, campaign=None, attachment_path=None):
        """Callback function for scheduler to send emails"""
        return email_manager.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachment_path=attachment_path,
            username=username,
            campaign=campaign
        )
    
    # Start the background scheduler
    scheduler.start_background_scheduler(send_email_callback)
    
    print("✅ Scheduler is running and checking for emails every 30 seconds")
    print("📊 Current schedule:")
    
    # Show initial stats
    stats = scheduler.get_schedule_stats()
    print(f"  - Pending: {stats['pending']}")
    print(f"  - Sent today: {stats['sent']}")
    print(f"  - Failed: {stats['failed']}")
    
    if stats['next_scheduled']:
        next_time = datetime.fromisoformat(stats['next_scheduled'])
        print(f"  - Next email: {next_time.strftime('%I:%M %p PT')}")
    
    print("\n" + "="*50)
    print("Monitoring... (updates will appear as emails are processed)")
    print("="*50 + "\n")
    
    try:
        # Keep the main thread running
        while True:
            time.sleep(60)  # Check every minute for status updates
            
            # Periodically show status
            stats = scheduler.get_schedule_stats()
            if stats['pending'] > 0:
                pacific_tz = ZoneInfo("US/Pacific")
                now = datetime.now(pacific_tz)
                print(f"[{now.strftime('%I:%M %p')}] Status: {stats['pending']} pending, {stats['sent']} sent today")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopping scheduler...")
        scheduler.stop_background_scheduler()
        print("✅ Scheduler stopped")

if __name__ == "__main__":
    main()