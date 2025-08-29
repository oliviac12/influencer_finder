"""
Email Tracking Integration for Streamlit App
Connects to your tracking service and manages email send/open data
"""
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

class EmailTrackingManager:
    def __init__(self, tracking_domain="https://tracking.unsettled.xyz"):
        self.tracking_domain = tracking_domain
        self.sent_emails_db = "cache/sent_emails_tracking.json"
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Create tracking database if it doesn't exist"""
        if not os.path.exists(self.sent_emails_db):
            os.makedirs(os.path.dirname(self.sent_emails_db), exist_ok=True)
            with open(self.sent_emails_db, 'w') as f:
                json.dump({"emails": {}}, f)
    
    def generate_tracking_id(self, username, campaign, timestamp=None):
        """Generate unique tracking ID for an email"""
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        # Create a unique but readable ID
        tracking_id = f"{campaign}_{username}_{timestamp[:10]}"
        # Add hash for uniqueness
        hash_suffix = hashlib.md5(f"{tracking_id}{timestamp}".encode()).hexdigest()[:6]
        return f"{tracking_id}_{hash_suffix}"
    
    def get_tracking_pixel_html(self, username, campaign, recipient_email=None, is_preview=False):
        """Generate HTML for tracking pixel and log sent email
        
        Args:
            username: Creator username
            campaign: Campaign name
            recipient_email: Recipient's email address
            is_preview: If True, marks this as a sender preview (won't count in recipient stats)
        """
        tracking_id = self.generate_tracking_id(username, campaign)
        
        # Save to our local database
        self.log_email_sent(tracking_id, username, campaign)
        
        # Also log to remote tracking service
        try:
            response = requests.post(
                f"{self.tracking_domain}/track/sent",
                json={
                    "email_id": tracking_id,
                    "campaign": campaign,
                    "recipient_email": recipient_email or "",
                    "username": username
                },
                timeout=2
            )
        except Exception as e:
            # Don't fail if tracking service is down
            print(f"Warning: Could not log sent email to tracking service: {e}")
        
        # Return tracking pixel HTML with all parameters
        pixel_url = f"{self.tracking_domain}/track/open?id={tracking_id}&campaign={campaign}&username={username}"
        if recipient_email:
            pixel_url += f"&recipient_email={recipient_email}"
        
        # Add sender flag for preview emails
        if is_preview:
            pixel_url += "&sender=true"
        
        return f'<img src="{pixel_url}" width="1" height="1" style="display:none;">', tracking_id
    
    def log_email_sent(self, tracking_id, username, campaign):
        """Log that an email was sent"""
        with open(self.sent_emails_db, 'r') as f:
            db = json.load(f)
        
        db["emails"][tracking_id] = {
            "username": username,
            "campaign": campaign,
            "sent_at": datetime.now().isoformat(),
            "opened": False,
            "open_count": 0,
            "first_opened_at": None,
            "last_opened_at": None
        }
        
        with open(self.sent_emails_db, 'w') as f:
            json.dump(db, f, indent=2)
    
    def fetch_tracking_stats(self):
        """Fetch latest stats from tracking service"""
        try:
            response = requests.get(f"{self.tracking_domain}/api/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": "Failed to fetch stats"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fetch_campaign_stats(self, campaign_name):
        """Fetch stats for specific campaign"""
        try:
            response = requests.get(f"{self.tracking_domain}/api/campaign/{campaign_name}", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": "Campaign not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sync_open_data(self):
        """Sync open data from tracking service with local database"""
        stats = self.fetch_tracking_stats()
        
        if stats.get("success"):
            # Update local database with open information
            # This is where we'd match tracking IDs to see who opened
            # For now, we'll just return the stats
            return stats
        
        return None
    
    def get_creator_email_status(self, username, campaign):
        """Get email status for a specific creator"""
        with open(self.sent_emails_db, 'r') as f:
            db = json.load(f)
        
        # Find emails for this creator/campaign
        creator_emails = []
        for tracking_id, data in db["emails"].items():
            if data["username"] == username and data["campaign"] == campaign:
                creator_emails.append({
                    "tracking_id": tracking_id,
                    **data
                })
        
        return creator_emails
    
    def get_campaign_email_report(self, campaign):
        """Get complete email report for a campaign"""
        with open(self.sent_emails_db, 'r') as f:
            db = json.load(f)
        
        # Filter by campaign
        campaign_emails = {}
        for tracking_id, data in db["emails"].items():
            if data["campaign"] == campaign:
                username = data["username"]
                if username not in campaign_emails:
                    campaign_emails[username] = []
                campaign_emails[username].append(data)
        
        # Calculate stats
        total_sent = len(campaign_emails)
        
        # Fetch open data from tracking service
        tracking_stats = self.fetch_campaign_stats(campaign)
        
        return {
            "campaign": campaign,
            "total_sent": total_sent,
            "creators": campaign_emails,
            "tracking_stats": tracking_stats
        }


# Future: Email Reply Management with Zoho
class ZohoReplyManager:
    """
    Future functionality for managing email replies via Zoho
    This will integrate with Zoho Mail API to:
    1. Fetch replies from your Zoho inbox
    2. Generate AI responses using Claude
    3. Send follow-ups via existing Zoho SMTP
    """
    
    def __init__(self):
        # Future: Connect to Zoho Mail API
        self.zoho_api_key = os.getenv('ZOHO_API_KEY')
        self.zoho_account_id = os.getenv('ZOHO_ACCOUNT_ID')
        self.api_base = "https://mail.zoho.com/api/accounts"
    
    def fetch_replies(self, campaign):
        """
        Future: Fetch email replies for a campaign from Zoho
        Uses Zoho Mail API to get inbox messages
        """
        # Will use Zoho Mail API endpoints:
        # GET /api/accounts/{accountId}/messages
        # Filters by subject line containing campaign name
        return []
    
    def generate_ai_response(self, original_email, reply_content, creator_data):
        """
        Future: Use Claude to generate appropriate response
        Maintains Wonder brand voice and campaign context
        """
        # This will use Claude to generate contextual responses
        # based on the creator's reply and Wonder's campaign goals
        pass
    
    def send_follow_up(self, to_email, subject, body):
        """
        Future: Send follow-up emails via existing Zoho SMTP
        Uses the same SMTP configuration already working
        """
        # Will reuse existing SMTP setup from email_outreach.py
        # No additional configuration needed
        pass


# Test the tracking integration
if __name__ == "__main__":
    # Initialize manager
    tracker = EmailTrackingManager("https://tracking.unsettled.xyz")
    
    # Test generating tracking pixel
    pixel_html, tracking_id = tracker.get_tracking_pixel_html("test_creator", "wonder_fall2025")
    print(f"📧 Tracking pixel HTML: {pixel_html[:50]}...")
    print(f"🆔 Tracking ID: {tracking_id}")
    
    # Test fetching stats (will fail if service not deployed)
    stats = tracker.fetch_tracking_stats()
    print(f"📊 Stats: {stats}")
    
    # Test getting creator status
    status = tracker.get_creator_email_status("test_creator", "wonder_fall2025")
    print(f"✉️ Creator email status: {status}")