#!/usr/bin/env python3
"""
Send all overdue scheduled emails immediately
"""
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_scheduler import EmailScheduler
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

def send_email(to_email, subject, body):
    """Send email using SMTP"""
    from_email = os.getenv('SMTP_EMAIL')
    from_password = os.getenv('SMTP_PASSWORD')
    
    if not from_email or not from_password:
        return False, "Email credentials not configured"
    
    # Get SMTP settings from env or use Zoho defaults
    smtp_host = os.getenv('SMTP_HOST', 'smtp.zoho.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add text version
        message.attach(MIMEText(body, 'plain'))
        
        # SMTP setup
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        
        # Send email
        text = message.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        return True, "Email sent successfully!"
        
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def main():
    print("🚀 Processing scheduled emails...")
    
    # Initialize scheduler
    scheduler = EmailScheduler(timezone="US/Pacific")
    
    # Get emails that should be sent now
    emails_to_send = scheduler.get_emails_to_send_now()
    
    if not emails_to_send:
        print("✅ No emails due to be sent right now")
        
        # Show schedule stats
        stats = scheduler.get_schedule_stats()
        if stats['pending'] > 0:
            print(f"\n📊 {stats['pending']} emails scheduled for later")
    else:
        print(f"\n📬 Sending {len(emails_to_send)} overdue emails...")
        
        success_count = 0
        failed_count = 0
        
        for email_data in emails_to_send:
            print(f"\n  Sending to: {email_data['to_email']}")
            
            try:
                # Send email directly using SMTP
                success, message = send_email(
                    email_data['to_email'],
                    email_data['subject'],
                    email_data['body']
                )
                
                if success:
                    scheduler.mark_as_sent(email_data['schedule_id'])
                    print(f"  ✅ Sent successfully!")
                    success_count += 1
                else:
                    scheduler.mark_as_failed(email_data['schedule_id'], message)
                    print(f"  ❌ Failed: {message}")
                    failed_count += 1
            except Exception as e:
                scheduler.mark_as_failed(email_data['schedule_id'], str(e))
                print(f"  ❌ Error: {e}")
                failed_count += 1
        
        print(f"\n📊 Results: {success_count} sent, {failed_count} failed")

if __name__ == "__main__":
    main()