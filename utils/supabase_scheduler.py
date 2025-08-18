"""
Supabase Email Scheduler
Replaces JSON file storage with Supabase database
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
from supabase import create_client, Client
from zoneinfo import ZoneInfo

class SupabaseEmailScheduler:
    def __init__(self):
        # Get credentials from environment
        url = os.getenv('SUPABASE_URL', 'https://jvyachugejlsvrwzscoi.supabase.co')
        key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp2eWFjaHVnZWpsc3Zyd3pzY29pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU0Nzc0ODgsImV4cCI6MjA3MTA1MzQ4OH0.irmZDdtwmd1pe5Ws_EIU1TNzCZP1no3WGxBEtZh552k')
        
        self.supabase: Client = create_client(url, key)
        self.timezone = ZoneInfo("US/Pacific")
    
    def schedule_email(self, 
                      email_id: str,
                      username: str,
                      campaign: str,
                      to_email: str,
                      subject: str,
                      body: str,
                      scheduled_time: datetime,
                      attachment_path: str = None) -> str:
        """Schedule an email in Supabase"""
        
        # Ensure scheduled_time has timezone
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=self.timezone)
        
        email_data = {
            'email_id': email_id,
            'username': username,
            'campaign': campaign,
            'to_email': to_email,
            'subject': subject,
            'body': body,
            'scheduled_time': scheduled_time.isoformat(),
            'status': 'pending',
            'attachment_path': attachment_path
        }
        
        try:
            result = self.supabase.table('scheduled_emails').insert(email_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"Error scheduling email: {e}")
            return None
    
    def schedule_bulk_emails(self,
                           emails: List[Dict],
                           campaign: str,
                           start_time: datetime,
                           interval_minutes: int = 5) -> List[str]:
        """Schedule multiple emails with intervals"""
        schedule_ids = []
        current_time = start_time
        
        for email in emails:
            schedule_id = self.schedule_email(
                email_id=email.get('email_id', f"{campaign}_{email['username']}"),
                username=email['username'],
                campaign=campaign,
                to_email=email['email'],
                subject=email['subject'],
                body=email['body'],
                scheduled_time=current_time,
                attachment_path=email.get('attachment_path')
            )
            if schedule_id:
                schedule_ids.append(str(schedule_id))
            
            # Add interval for next email
            from datetime import timedelta
            current_time = current_time + timedelta(minutes=interval_minutes)
        
        return schedule_ids
    
    def get_pending_emails(self) -> List[Dict]:
        """Get all pending emails"""
        try:
            result = self.supabase.table('scheduled_emails')\
                .select('*')\
                .eq('status', 'pending')\
                .order('scheduled_time')\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting pending emails: {e}")
            return []
    
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
            print(f"Error getting emails to send: {e}")
            return []
    
    def mark_as_sent(self, email_id: int):
        """Mark email as sent"""
        try:
            self.supabase.table('scheduled_emails')\
                .update({
                    'status': 'sent',
                    'sent_at': datetime.now(self.timezone).isoformat()
                })\
                .eq('id', email_id)\
                .execute()
        except Exception as e:
            print(f"Error marking email as sent: {e}")
    
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
        except Exception as e:
            print(f"Error marking email as failed: {e}")
    
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
            
            # Get next scheduled email
            next_email = self.supabase.table('scheduled_emails')\
                .select('scheduled_time')\
                .eq('status', 'pending')\
                .order('scheduled_time')\
                .limit(1)\
                .execute()
            
            return {
                'pending': pending.count if pending.count else 0,
                'sent': sent.count if sent.count else 0,
                'failed': failed.count if failed.count else 0,
                'total': (pending.count or 0) + (sent.count or 0) + (failed.count or 0),
                'next_scheduled': next_email.data[0]['scheduled_time'] if next_email.data else None
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'pending': 0, 'sent': 0, 'failed': 0, 'total': 0, 'next_scheduled': None}
    
    def get_campaign_schedule(self, campaign: str) -> List[Dict]:
        """Get all emails for a campaign"""
        try:
            result = self.supabase.table('scheduled_emails')\
                .select('*')\
                .eq('campaign', campaign)\
                .order('scheduled_time')\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"Error getting campaign schedule: {e}")
            return []
    
    def cancel_scheduled_email(self, email_id: int) -> bool:
        """Cancel a scheduled email"""
        try:
            self.supabase.table('scheduled_emails')\
                .update({'status': 'cancelled'})\
                .eq('id', email_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error cancelling email: {e}")
            return False