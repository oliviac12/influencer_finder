"""
Email Scheduler
Manages scheduled email sending with persistent storage
Works both locally (while running) and when deployed
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time
from enum import Enum
from zoneinfo import ZoneInfo  # Python 3.9+ for timezone support


class ScheduleStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EmailScheduler:
    def __init__(self, schedule_file="cache/scheduled_emails.json", timezone="US/Pacific"):
        self.schedule_file = schedule_file
        self.scheduled_emails = self.load_schedule()
        self.scheduler_thread = None
        self.running = False
        self.timezone = ZoneInfo(timezone)  # Default to Pacific Time
        
    def load_schedule(self) -> dict:
        """Load scheduled emails from file"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_schedule(self):
        """Save schedule to file"""
        os.makedirs(os.path.dirname(self.schedule_file), exist_ok=True)
        with open(self.schedule_file, 'w') as f:
            json.dump(self.scheduled_emails, f, indent=2, default=str)
    
    def schedule_email(self, 
                       email_id: str,
                       username: str,
                       campaign: str,
                       to_email: str,
                       subject: str,
                       body: str,
                       scheduled_time: datetime,
                       attachment_path: str = None) -> str:
        """Schedule an email to be sent at a specific time"""
        
        schedule_id = f"{campaign}_{username}_{scheduled_time.isoformat()}"
        
        self.scheduled_emails[schedule_id] = {
            'email_id': email_id,
            'username': username,
            'campaign': campaign,
            'to_email': to_email,
            'subject': subject,
            'body': body,
            'scheduled_time': scheduled_time.isoformat(),
            'attachment_path': attachment_path,
            'status': ScheduleStatus.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'attempts': 0
        }
        
        self.save_schedule()
        return schedule_id
    
    def schedule_bulk_emails(self,
                           emails: List[Dict],
                           campaign: str,
                           start_time: datetime,
                           interval_minutes: int = 5) -> List[str]:
        """Schedule multiple emails with intervals between them"""
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
            schedule_ids.append(schedule_id)
            
            # Add interval for next email
            current_time = current_time + timedelta(minutes=interval_minutes)
        
        return schedule_ids
    
    def cancel_scheduled_email(self, schedule_id: str) -> bool:
        """Cancel a scheduled email"""
        if schedule_id in self.scheduled_emails:
            self.scheduled_emails[schedule_id]['status'] = ScheduleStatus.CANCELLED.value
            self.scheduled_emails[schedule_id]['cancelled_at'] = datetime.now().isoformat()
            self.save_schedule()
            return True
        return False
    
    def get_pending_emails(self) -> List[Dict]:
        """Get all pending scheduled emails"""
        pending = []
        now = datetime.now(self.timezone)  # Use timezone-aware now
        
        for schedule_id, email_data in self.scheduled_emails.items():
            if email_data['status'] == ScheduleStatus.PENDING.value:
                scheduled_time = datetime.fromisoformat(email_data['scheduled_time'])
                # Ensure scheduled_time has timezone info
                if scheduled_time.tzinfo is None:
                    scheduled_time = scheduled_time.replace(tzinfo=self.timezone)
                
                # Include if scheduled for the future or within last hour (in case of app restart)
                if scheduled_time > now - timedelta(hours=1):
                    email_data['schedule_id'] = schedule_id
                    email_data['scheduled_datetime'] = scheduled_time
                    pending.append(email_data)
        
        # Sort by scheduled time
        pending.sort(key=lambda x: x['scheduled_datetime'])
        return pending
    
    def get_emails_to_send_now(self) -> List[Dict]:
        """Get emails that should be sent now"""
        emails_to_send = []
        now = datetime.now(self.timezone)  # Get current time in Pacific
        
        for schedule_id, email_data in self.scheduled_emails.items():
            if email_data['status'] == ScheduleStatus.PENDING.value:
                # Parse scheduled time and ensure it has timezone info
                scheduled_time = datetime.fromisoformat(email_data['scheduled_time'])
                if scheduled_time.tzinfo is None:
                    # If no timezone, assume it was meant to be Pacific
                    scheduled_time = scheduled_time.replace(tzinfo=self.timezone)
                
                # Send if scheduled time has passed
                if scheduled_time <= now:
                    email_data['schedule_id'] = schedule_id
                    emails_to_send.append(email_data)
        
        return emails_to_send
    
    def mark_as_sent(self, schedule_id: str):
        """Mark email as sent"""
        if schedule_id in self.scheduled_emails:
            self.scheduled_emails[schedule_id]['status'] = ScheduleStatus.SENT.value
            self.scheduled_emails[schedule_id]['sent_at'] = datetime.now().isoformat()
            self.save_schedule()
    
    def mark_as_failed(self, schedule_id: str, error: str):
        """Mark email as failed"""
        if schedule_id in self.scheduled_emails:
            email = self.scheduled_emails[schedule_id]
            email['status'] = ScheduleStatus.FAILED.value
            email['attempts'] = email.get('attempts', 0) + 1
            email['last_error'] = error
            email['failed_at'] = datetime.now().isoformat()
            
            # Retry logic: reschedule if less than 3 attempts
            if email['attempts'] < 3:
                # Reschedule for 30 minutes later
                new_time = datetime.now(self.timezone) + timedelta(minutes=30)
                email['scheduled_time'] = new_time.isoformat()
                email['status'] = ScheduleStatus.PENDING.value
                email['retry_scheduled'] = True
            
            self.save_schedule()
    
    def get_campaign_schedule(self, campaign: str) -> List[Dict]:
        """Get all scheduled emails for a campaign"""
        campaign_emails = []
        
        for schedule_id, email_data in self.scheduled_emails.items():
            if email_data.get('campaign') == campaign:
                email_data['schedule_id'] = schedule_id
                email_data['scheduled_datetime'] = datetime.fromisoformat(email_data['scheduled_time'])
                campaign_emails.append(email_data)
        
        campaign_emails.sort(key=lambda x: x['scheduled_datetime'])
        return campaign_emails
    
    def get_schedule_stats(self) -> Dict:
        """Get statistics about scheduled emails"""
        stats = {
            'total': len(self.scheduled_emails),
            'pending': 0,
            'sent': 0,
            'failed': 0,
            'cancelled': 0,
            'next_scheduled': None
        }
        
        next_time = None
        now = datetime.now(self.timezone)  # Use timezone-aware now
        
        for email_data in self.scheduled_emails.values():
            status = email_data['status']
            if status == ScheduleStatus.PENDING.value:
                stats['pending'] += 1
                scheduled_time = datetime.fromisoformat(email_data['scheduled_time'])
                # Ensure scheduled_time has timezone info
                if scheduled_time.tzinfo is None:
                    scheduled_time = scheduled_time.replace(tzinfo=self.timezone)
                if scheduled_time > now:
                    if next_time is None:
                        next_time = scheduled_time
                    else:
                        # Ensure next_time also has timezone info for comparison
                        if next_time.tzinfo is None:
                            next_time = next_time.replace(tzinfo=self.timezone)
                        if scheduled_time < next_time:
                            next_time = scheduled_time
            elif status == ScheduleStatus.SENT.value:
                stats['sent'] += 1
            elif status == ScheduleStatus.FAILED.value:
                stats['failed'] += 1
            elif status == ScheduleStatus.CANCELLED.value:
                stats['cancelled'] += 1
        
        if next_time:
            stats['next_scheduled'] = next_time.isoformat()
        
        return stats
    
    def start_background_scheduler(self, email_send_callback):
        """Start background thread to process scheduled emails"""
        if self.running:
            return
        
        self.running = True
        self.email_send_callback = email_send_callback
        
        def run_scheduler():
            while self.running:
                try:
                    # Check for emails to send
                    emails_to_send = self.get_emails_to_send_now()
                    
                    for email_data in emails_to_send:
                        try:
                            # Call the email sending callback
                            success, message = self.email_send_callback(
                                to_email=email_data['to_email'],
                                subject=email_data['subject'],
                                body=email_data['body'],
                                username=email_data.get('username'),
                                campaign=email_data.get('campaign'),
                                attachment_path=email_data.get('attachment_path')
                            )
                            
                            if success:
                                self.mark_as_sent(email_data['schedule_id'])
                                print(f"✅ Sent scheduled email to {email_data['to_email']}")
                            else:
                                self.mark_as_failed(email_data['schedule_id'], message)
                                print(f"❌ Failed to send to {email_data['to_email']}: {message}")
                                
                        except Exception as e:
                            self.mark_as_failed(email_data['schedule_id'], str(e))
                            print(f"❌ Error sending scheduled email: {e}")
                    
                    # Sleep for 30 seconds before checking again
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"Scheduler error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("📅 Background email scheduler started")
    
    def stop_background_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("📅 Background email scheduler stopped")


# Test the scheduler
if __name__ == "__main__":
    scheduler = EmailScheduler()
    
    # Schedule a test email for 2 minutes from now
    test_time = datetime.now() + timedelta(minutes=2)
    schedule_id = scheduler.schedule_email(
        email_id="test_001",
        username="testcreator",
        campaign="test_campaign",
        to_email="test@example.com",
        subject="Test Scheduled Email",
        body="This is a test of the scheduling system",
        scheduled_time=test_time
    )
    
    print(f"Scheduled email with ID: {schedule_id}")
    print(f"Scheduled for: {test_time}")
    
    # Get pending emails
    pending = scheduler.get_pending_emails()
    print(f"\nPending emails: {len(pending)}")
    for email in pending:
        print(f"  - To: {email['to_email']} at {email['scheduled_time']}")
    
    # Get stats
    stats = scheduler.get_schedule_stats()
    print(f"\nSchedule stats: {stats}")