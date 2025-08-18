#!/usr/bin/env python
"""
Standalone Supabase Email Scheduler for Replit
Everything in one file - no imports needed
"""
import os
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional

# Install required packages if not available
try:
    from supabase import create_client, Client
    from zoneinfo import ZoneInfo
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(['pip', 'install', 'supabase', '--quiet'])
    from supabase import create_client, Client
    from zoneinfo import ZoneInfo

class SupabaseEmailScheduler:
    def __init__(self):
        # Get credentials from environment
        url = os.getenv('SUPABASE_URL', 'https://jvyachugejlsvrwzscoi.supabase.co')
        key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp2eWFjaHVnZWpsc3Zyd3pzY29pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU0Nzc0ODgsImV4cCI6MjA3MTA1MzQ4OH0.irmZDdtwmd1pe5Ws_EIU1TNzCZP1no3WGxBEtZh552k')
        
        try:
            self.supabase: Client = create_client(url, key)
            self.timezone = ZoneInfo("US/Pacific")
            print("✅ Connected to Supabase")
        except Exception as e:
            print(f"❌ Supabase connection error: {e}")
            raise
    
    def get_emails_to_send_now(self) -> List[Dict]:
        """Get emails that should be sent now"""
        now = datetime.now(self.timezone)
        
        try:
            result = self.supabase.table('scheduled_emails')\
                .select('*')\
                .eq('status', 'pending')\
                .lte('scheduled_time', now.isoformat())\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ Error getting emails to send: {e}")
            return []
    
    def mark_as_sent(self, email_id: int):
        """Mark email as sent and create permanent record"""
        try:
            sent_time = datetime.now(self.timezone).isoformat()
            
            # Get the original email data
            scheduled_email = self.supabase.table('scheduled_emails')\
                .select('*')\
                .eq('id', email_id)\
                .execute()
            
            if scheduled_email.data:
                email_data = scheduled_email.data[0]
                
                # Create permanent record in sent_emails table
                self.supabase.table('sent_emails').insert({
                    'email_id': email_data.get('email_id'),
                    'username': email_data.get('username'),
                    'campaign': email_data.get('campaign'),
                    'to_email': email_data.get('to_email'),
                    'subject': email_data.get('subject'),
                    'body': email_data.get('body'),
                    'scheduled_time': email_data.get('scheduled_time'),
                    'sent_at': sent_time,
                    'attachment_path': email_data.get('attachment_path')
                }).execute()
            
            # Update scheduled_emails status
            self.supabase.table('scheduled_emails')\
                .update({
                    'status': 'sent',
                    'sent_at': sent_time
                })\
                .eq('id', email_id)\
                .execute()
                
            print(f"✅ Marked email {email_id} as sent")
        except Exception as e:
            print(f"❌ Error marking email as sent: {e}")
    
    def mark_as_failed(self, email_id: int, error: str):
        """Mark email as failed"""
        try:
            self.supabase.table('scheduled_emails')\
                .update({
                    'status': 'failed',
                    'error_message': error,
                    'failed_at': datetime.now(self.timezone).isoformat()
                })\
                .eq('id', email_id)\
                .execute()
            print(f"❌ Marked email {email_id} as failed")
        except Exception as e:
            print(f"❌ Error marking email as failed: {e}")
    
    def get_schedule_stats(self) -> Dict:
        """Get statistics about scheduled emails"""
        try:
            # Get counts by status
            pending = self.supabase.table('scheduled_emails')\
                .select('id', count='exact')\
                .eq('status', 'pending')\
                .execute()
            
            sent = self.supabase.table('scheduled_emails')\
                .select('id', count='exact')\
                .eq('status', 'sent')\
                .execute()
            
            failed = self.supabase.table('scheduled_emails')\
                .select('id', count='exact')\
                .eq('status', 'failed')\
                .execute()
            
            return {
                'pending': pending.count if pending.count else 0,
                'sent': sent.count if sent.count else 0,
                'failed': failed.count if failed.count else 0,
                'total': (pending.count or 0) + (sent.count or 0) + (failed.count or 0)
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {'pending': 0, 'sent': 0, 'failed': 0, 'total': 0}

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
    print("📧 Standalone Supabase Email Scheduler")
    print("🔗 Connecting to Supabase database...")
    print("="*50)
    
    try:
        # Initialize Supabase scheduler
        scheduler = SupabaseEmailScheduler()
        
        print("🚀 Scheduler started - checking every 30 seconds")
        print("📊 Will show status every 3 minutes")
        print("="*50)
        
        while True:
            try:
                now = datetime.now()
                
                # Get emails that need to be sent
                emails_to_send = scheduler.get_emails_to_send_now()
                
                if emails_to_send:
                    print(f"\n📬 Found {len(emails_to_send)} emails to send")
                    
                    for email_data in emails_to_send:
                        print(f"📧 Sending to {email_data['to_email']}")
                        
                        success = send_email(
                            email_data['to_email'],
                            email_data['subject'],
                            email_data['body']
                        )
                        
                        if success:
                            scheduler.mark_as_sent(email_data['id'])
                        else:
                            scheduler.mark_as_failed(email_data['id'], "SMTP send failed")
                
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
                print(f"❌ Error in main loop: {e}")
                print("⏳ Waiting 60 seconds before retry...")
                time.sleep(60)  # Wait longer on error
                
    except Exception as e:
        print(f"❌ Failed to initialize scheduler: {e}")
        print("🔧 Check your Supabase credentials and internet connection")

if __name__ == "__main__":
    main()