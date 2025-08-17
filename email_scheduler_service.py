#!/usr/bin/env python3
"""
Email Scheduler Service - Simplified version
Continuously processes scheduled emails in the background
"""
import sys
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.email_scheduler import EmailScheduler
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.email_tracking_integration import EmailTrackingManager

# Load environment variables
load_dotenv()

def send_email_with_tracking(to_email, subject, body, username=None, campaign=None, attachment_path=None):
    """Send email using SMTP with tracking"""
    from_email = os.getenv('SMTP_EMAIL')
    from_password = os.getenv('SMTP_PASSWORD')
    
    if not from_email or not from_password:
        return False, "Email credentials not configured"
    
    # Get SMTP settings from env or use Zoho defaults
    smtp_host = os.getenv('SMTP_HOST', 'smtp.zoho.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    # Add tracking pixel if username and campaign provided
    tracking_id = None
    if username and campaign:
        tracker = EmailTrackingManager()
        pixel_html, tracking_id = tracker.get_tracking_pixel_html(username, campaign, recipient_email=to_email)
        # Convert body to HTML and add tracking pixel
        html_body = f"""
        <html>
        <body>
        {body.replace(chr(10), '<br>')}
        <br>
        {pixel_html}
        </body>
        </html>
        """
    else:
        html_body = None
    
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add both plain text and HTML versions
        message.attach(MIMEText(body, 'plain'))
        if html_body:
            message.attach(MIMEText(html_body, 'html'))
        
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
    print("📧 Email Scheduler Service Starting...")
    print("Press Ctrl+C to stop\n")
    
    # Initialize scheduler
    scheduler = EmailScheduler(timezone="US/Pacific")
    
    # Start the background scheduler with our send callback
    scheduler.start_background_scheduler(send_email_with_tracking)
    
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