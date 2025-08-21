"""
Zoho Native Email Scheduler
Uses Zoho Mail's built-in scheduling functionality instead of external schedulers
Much simpler and more reliable than Replit-based scheduling
"""
import os
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo
import time


class ZohoNativeScheduler:
    """
    Use Zoho Mail's native scheduling capabilities via REST API
    No need for external schedulers or cron jobs!
    """
    
    def __init__(self):
        # Zoho OAuth credentials from environment
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')
        self.account_id = os.getenv('ZOHO_ACCOUNT_ID')
        
        # API endpoints
        self.auth_url = "https://accounts.zoho.com/oauth/v2/token"
        self.api_base = "https://mail.zoho.com/api"
        
        # Cache access token
        self._access_token = None
        self._token_expiry = None
        
        # Default timezone
        self.timezone = ZoneInfo("US/Pacific")
    
    def get_access_token(self) -> str:
        """Get or refresh OAuth access token"""
        # Check if we have a valid cached token
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._access_token
        
        # Get new access token using refresh token
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "scope": "ZohoMail.messages.ALL,ZohoMail.accounts.READ"
        }
        
        response = requests.post(self.auth_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self._access_token = token_data["access_token"]
            # Token expires in 1 hour, refresh 5 minutes early
            expires_in = token_data.get("expires_in", 3600)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            return self._access_token
        else:
            raise Exception(f"Failed to get access token: {response.text}")
    
    def schedule_email(self, 
                      to_email: str,
                      subject: str,
                      body: str,
                      scheduled_time: datetime,
                      from_address: str = None,
                      attachment_path: str = None,
                      campaign: str = None,
                      username: str = None) -> Dict:
        """
        Schedule an email using Zoho Mail's native scheduling
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: HTML email body
            scheduled_time: When to send the email (datetime object)
            from_address: Sender email (defaults to account email)
            attachment_path: Optional path to attachment file
            campaign: Campaign identifier for tracking
            username: Creator username for tracking
        
        Returns:
            Response from Zoho API with email ID
        """
        
        # Ensure scheduled_time has timezone
        if scheduled_time.tzinfo is None:
            scheduled_time = scheduled_time.replace(tzinfo=self.timezone)
        
        # Get access token
        access_token = self.get_access_token()
        
        # Prepare headers
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        
        # Convert scheduled time to Zoho format (MM/DD/YYYY HH:MM:SS)
        schedule_str = scheduled_time.strftime("%m/%d/%Y %H:%M:%S")
        
        # Map timezone to Zoho format
        timezone_map = {
            "US/Pacific": "GMT -8:00 (Pacific Standard Time - America/Los Angeles)",
            "US/Eastern": "GMT -5:00 (Eastern Standard Time - America/New York)",
            "Asia/Shanghai": "GMT +8:00 (China Standard Time - Asia/Shanghai)",
            "UTC": "GMT +0:00 (Greenwich Mean Time - UTC)"
        }
        zoho_timezone = timezone_map.get(str(scheduled_time.tzinfo), "GMT -8:00 (Pacific Standard Time - America/Los Angeles)")
        
        # Prepare email data
        email_data = {
            "fromAddress": from_address or os.getenv('SMTP_EMAIL'),
            "toAddress": to_email,
            "subject": subject,
            "content": body,
            "contentType": "html",
            
            # Scheduling parameters
            "scheduleType": "6",  # Custom schedule
            "timezone": zoho_timezone,
            "scheduleTime": schedule_str
        }
        
        # Add tracking headers if provided
        if campaign or username:
            email_data["mailHeaders"] = []
            if campaign:
                email_data["mailHeaders"].append({
                    "key": "X-Campaign",
                    "value": campaign
                })
            if username:
                email_data["mailHeaders"].append({
                    "key": "X-Creator-Username",
                    "value": username
                })
        
        # Handle attachments if provided
        if attachment_path and os.path.exists(attachment_path):
            # For attachments, we need to use multipart form data
            return self._send_with_attachment(email_data, attachment_path, headers)
        
        # Send API request
        url = f"{self.api_base}/accounts/{self.account_id}/messages"
        response = requests.post(url, headers=headers, json=email_data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Email scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M %Z')}")
            return {
                "success": True,
                "email_id": result.get("data", {}).get("messageId"),
                "scheduled_time": schedule_str,
                "response": result
            }
        else:
            print(f"❌ Failed to schedule email: {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def _send_with_attachment(self, email_data: Dict, attachment_path: str, headers: Dict) -> Dict:
        """Send email with attachment using multipart form data"""
        # Remove Content-Type from headers for multipart
        headers.pop("Content-Type", None)
        
        # Prepare multipart form data
        files = {
            'attachments': (os.path.basename(attachment_path), open(attachment_path, 'rb'))
        }
        
        # Convert email data to form fields
        data = {
            "messageData": json.dumps(email_data)
        }
        
        url = f"{self.api_base}/accounts/{self.account_id}/messages"
        response = requests.post(url, headers=headers, data=data, files=files)
        
        # Close file
        files['attachments'][1].close()
        
        if response.status_code in [200, 201]:
            result = response.json()
            return {
                "success": True,
                "email_id": result.get("data", {}).get("messageId"),
                "response": result
            }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    
    def schedule_bulk_emails(self,
                           emails: List[Dict],
                           campaign: str,
                           start_time: datetime,
                           interval_minutes: int = 5) -> List[str]:
        """
        Schedule multiple emails with intervals
        
        Args:
            emails: List of email dictionaries with to_email, subject, body
            campaign: Campaign identifier
            start_time: When to start sending
            interval_minutes: Minutes between each email
        
        Returns:
            List of scheduled email IDs
        """
        scheduled_ids = []
        current_time = start_time
        
        for i, email in enumerate(emails):
            # Schedule this email
            result = self.schedule_email(
                to_email=email['email'],
                subject=email['subject'],
                body=email['body'],
                scheduled_time=current_time,
                attachment_path=email.get('attachment_path'),
                campaign=campaign,
                username=email.get('username')
            )
            
            if result['success']:
                scheduled_ids.append(result['email_id'])
                print(f"  [{i+1}/{len(emails)}] Scheduled for @{email.get('username', 'unknown')} at {current_time.strftime('%H:%M')}")
            else:
                print(f"  [{i+1}/{len(emails)}] Failed to schedule for @{email.get('username', 'unknown')}")
            
            # Increment time for next email
            current_time += timedelta(minutes=interval_minutes)
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        return scheduled_ids
    
    def cancel_scheduled_email(self, email_id: str) -> bool:
        """
        Cancel a scheduled email
        Note: This might require moving the email to trash or using a different API endpoint
        """
        access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }
        
        # Try to delete/cancel the scheduled email
        url = f"{self.api_base}/accounts/{self.account_id}/messages/{email_id}"
        response = requests.delete(url, headers=headers)
        
        if response.status_code in [200, 204]:
            print(f"✅ Cancelled scheduled email {email_id}")
            return True
        else:
            print(f"❌ Failed to cancel email {email_id}: {response.text}")
            return False
    
    def get_scheduled_emails(self) -> List[Dict]:
        """
        Get list of scheduled emails
        Note: May need to query drafts/outbox folder with schedule status
        """
        access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }
        
        # Query scheduled emails (might be in drafts or special folder)
        url = f"{self.api_base}/accounts/{self.account_id}/folders/drafts/messages"
        params = {
            "limit": 100,
            "status": "scheduled"  # This might vary based on Zoho's API
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"Failed to get scheduled emails: {response.text}")
            return []


# Simple interface functions for easy integration
def schedule_email_with_zoho(to_email: str, subject: str, body: str, 
                            scheduled_time: datetime, **kwargs) -> Dict:
    """Simple function to schedule an email with Zoho"""
    scheduler = ZohoNativeScheduler()
    return scheduler.schedule_email(to_email, subject, body, scheduled_time, **kwargs)


def schedule_bulk_with_zoho(emails: List[Dict], campaign: str, 
                           start_time: datetime, interval_minutes: int = 5) -> List[str]:
    """Simple function to schedule bulk emails with Zoho"""
    scheduler = ZohoNativeScheduler()
    return scheduler.schedule_bulk_emails(emails, campaign, start_time, interval_minutes)


if __name__ == "__main__":
    # Example usage
    from datetime import datetime, timedelta
    
    # Initialize scheduler
    scheduler = ZohoNativeScheduler()
    
    # Schedule a single email for 1 hour from now
    scheduled_time = datetime.now() + timedelta(hours=1)
    
    result = scheduler.schedule_email(
        to_email="test@example.com",
        subject="Test Scheduled Email",
        body="<html><body><h1>Test</h1><p>This email was scheduled using Zoho's native scheduling.</p></body></html>",
        scheduled_time=scheduled_time,
        campaign="test_campaign",
        username="test_user"
    )
    
    if result['success']:
        print(f"✅ Email scheduled successfully!")
        print(f"Email ID: {result['email_id']}")
    else:
        print(f"❌ Failed to schedule email")
        print(f"Error: {result['error']}")