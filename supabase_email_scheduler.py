#!/usr/bin/env python
"""
Supabase Email Scheduler for Replit
No GitHub syncing needed - uses Supabase database
"""
import os
import time
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.supabase_scheduler import SupabaseEmailScheduler

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

def main():
    print("📧 Supabase Email Scheduler")
    print("🔗 Connected to Supabase database")
    print("="*50)
    
    # Initialize Supabase scheduler
    scheduler = SupabaseEmailScheduler()
    
    while True:
        try:
            now = datetime.now()
            
            # Get emails that need to be sent
            emails_to_send = scheduler.get_emails_to_send_now()
            
            if emails_to_send:
                print(f"📬 Found {len(emails_to_send)} emails to send")
                
                for email_data in emails_to_send:
                    print(f"📧 Sending to {email_data['to_email']}")
                    
                    success = send_email(
                        email_data['to_email'],
                        email_data['subject'],
                        email_data['body']
                    )
                    
                    if success:
                        scheduler.mark_as_sent(email_data['id'])
                        print(f"✅ Sent to {email_data['to_email']}")
                    else:
                        scheduler.mark_as_failed(email_data['id'], "SMTP send failed")
                        print(f"❌ Failed to send to {email_data['to_email']}")
            
            # Show periodic status
            if int(time.time()) % 180 == 0:  # Every 3 minutes
                stats = scheduler.get_schedule_stats()
                print(f"[{now.strftime('%I:%M %p PT')}] Status: {stats['pending']} pending, {stats['sent']} sent, {stats['failed']} failed")
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n⚠️ Stopping scheduler...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    main()