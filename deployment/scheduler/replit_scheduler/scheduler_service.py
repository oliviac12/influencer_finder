#!/usr/bin/env python3
"""
Minimal Email Scheduler for Replit
Works with Streamlit Cloud deployment
"""
import json
import os
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

# Configuration
GITHUB_REPO = "https://github.com/oliviac12/influencer_finder.git"
CHECK_INTERVAL = 60  # Check every minute

def setup_repo():
    """Clone or pull the repository"""
    if not os.path.exists("influencer_finder"):
        print("Cloning repository...")
        subprocess.run(["git", "clone", GITHUB_REPO])
    os.chdir("influencer_finder")
    subprocess.run(["git", "pull"])

def send_email(to_email, subject, body):
    """Send email via SMTP"""
    smtp_email = os.getenv('SMTP_EMAIL', 'olivia@unsettled.xyz')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_password:
        print("Error: SMTP_PASSWORD not set")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.zoho.com', 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def process_scheduled_emails():
    """Check and send due emails"""
    schedule_file = "cache/scheduled_emails.json"
    
    if not os.path.exists(schedule_file):
        return
    
    with open(schedule_file, 'r') as f:
        scheduled = json.load(f)
    
    now = datetime.now()
    updated = False
    
    for email_id, data in scheduled.items():
        if data['status'] == 'pending':
            scheduled_time = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
            
            if scheduled_time <= now:
                print(f"Sending email to {data['to_email']}...")
                
                if send_email(data['to_email'], data['subject'], data['body']):
                    data['status'] = 'sent'
                    data['sent_at'] = now.isoformat()
                    updated = True
                    print(f"✅ Sent to {data['to_email']}")
                else:
                    print(f"❌ Failed to send to {data['to_email']}")
    
    if updated:
        # Save and push changes
        with open(schedule_file, 'w') as f:
            json.dump(scheduled, f, indent=2)
        
        subprocess.run(["git", "add", schedule_file])
        subprocess.run(["git", "commit", "-m", "Update email status"])
        subprocess.run(["git", "push"])

def main():
    print("📧 Email Scheduler for Streamlit Cloud")
    print("="*40)
    
    setup_repo()
    
    while True:
        try:
            # Pull latest changes
            subprocess.run(["git", "pull"], capture_output=True)
            
            # Process emails
            process_scheduled_emails()
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()