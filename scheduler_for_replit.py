#!/usr/bin/env python
"""
Standalone Email Scheduler for Replit
Syncs with Streamlit Cloud app via GitHub
"""
import json
import os
import time
import smtplib
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

# Configuration
SCHEDULE_FILE = "cache/scheduled_emails.json"
CHECK_INTERVAL = 30  # Check every 30 seconds
SYNC_INTERVAL = 300  # Sync with GitHub every 5 minutes

def send_email(to_email, subject, body):
    """Send email via SMTP"""
    from_email = os.getenv('SMTP_EMAIL', 'olivia@unsettled.xyz')
    from_password = os.getenv('SMTP_PASSWORD')
    
    if not from_email or not from_password:
        print(f"❌ Missing email credentials")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Send via SMTP
        server = smtplib.SMTP('smtp.zoho.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Sent email to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def sync_from_github():
    """Pull latest scheduled emails from GitHub"""
    try:
        result = subprocess.run(['git', 'pull'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("📥 Synced from GitHub")
        return True
    except Exception as e:
        print(f"❌ Git pull error: {e}")
        return False

def sync_to_github():
    """Push email status updates to GitHub"""
    try:
        subprocess.run(['git', 'add', SCHEDULE_FILE], 
                      capture_output=True)
        result = subprocess.run(['git', 'commit', '-m', 
                               f'Update email status - {datetime.now().strftime("%H:%M")}'], 
                              capture_output=True)
        if result.returncode == 0:  # Only push if there were changes
            subprocess.run(['git', 'push'], capture_output=True)
            print("📤 Pushed status to GitHub")
        return True
    except Exception as e:
        print(f"❌ Git push error: {e}")
        return False

def process_scheduled_emails():
    """Check and send due emails"""
    if not os.path.exists(SCHEDULE_FILE):
        return 0
    
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            scheduled_emails = json.load(f)
    except Exception as e:
        print(f"❌ Error reading schedule: {e}")
        return 0
    
    pacific_tz = ZoneInfo("US/Pacific")
    now = datetime.now(pacific_tz)
    emails_sent = 0
    updated = False
    
    for email_id, data in scheduled_emails.items():
        if data.get('status') == 'pending':
            try:
                # Parse scheduled time
                scheduled_time_str = data['scheduled_time']
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                
                # Convert to Pacific timezone if needed
                if scheduled_time.tzinfo is None:
                    scheduled_time = scheduled_time.replace(tzinfo=pacific_tz)
                else:
                    scheduled_time = scheduled_time.astimezone(pacific_tz)
                
                # Check if it's time to send
                if scheduled_time <= now:
                    print(f"📧 Sending email to {data['to_email']}")
                    
                    if send_email(data['to_email'], data['subject'], data['body']):
                        # Mark as sent
                        data['status'] = 'sent'
                        data['sent_at'] = now.isoformat()
                        emails_sent += 1
                        updated = True
                    else:
                        # Mark as failed
                        data['status'] = 'failed'
                        data['failed_at'] = now.isoformat()
                        updated = True
                        
            except Exception as e:
                print(f"❌ Error processing email {email_id}: {e}")
    
    # Save changes if any
    if updated:
        try:
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump(scheduled_emails, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving schedule: {e}")
    
    return emails_sent

def main():
    print("📧 Email Scheduler for Streamlit Cloud")
    print("🔗 Syncing with GitHub every 5 minutes")
    print("⏰ Checking emails every 30 seconds")
    print("="*50)
    
    last_sync = 0
    
    while True:
        try:
            current_time = time.time()
            pacific_tz = ZoneInfo("US/Pacific")
            now = datetime.now(pacific_tz)
            
            # Sync from GitHub periodically
            if current_time - last_sync > SYNC_INTERVAL:
                sync_from_github()
                last_sync = current_time
            
            # Process scheduled emails
            emails_sent = process_scheduled_emails()
            
            # If we sent emails, push status back to GitHub
            if emails_sent > 0:
                sync_to_github()
                print(f"✅ Sent {emails_sent} emails at {now.strftime('%I:%M %p PT')}")
            
            # Show status every few minutes
            if int(current_time) % 180 == 0:  # Every 3 minutes
                print(f"[{now.strftime('%I:%M %p PT')}] Scheduler running...")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⚠️ Stopping scheduler...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    main()