"""
Email Cache System
Stores generated personalized emails to avoid regenerating them
"""
import json
import os
from datetime import datetime
from pathlib import Path

class EmailCache:
    def __init__(self, cache_file="cache/email_cache.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()
    
    def load_cache(self):
        """Load existing cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_cache(self):
        """Save cache to file"""
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_email_key(self, username, campaign_name):
        """Generate cache key for creator+campaign"""
        campaign_key = campaign_name.lower().replace(' ', '_')
        return f"{username}_{campaign_key}"
    
    def save_email(self, username, campaign_name, email_text):
        """Save generated email"""
        key = self.get_email_key(username, campaign_name)
        
        self.cache[key] = {
            'username': username,
            'campaign_name': campaign_name,
            'email_text': email_text,
            'generated_at': datetime.now().isoformat()
        }
        
        self.save_cache()
    
    def get_email(self, username, campaign_name):
        """Get cached email for creator+campaign"""
        key = self.get_email_key(username, campaign_name)
        cached = self.cache.get(key)
        if cached:
            return cached.get('email_text')
        return None
    
    def has_email(self, username, campaign_name):
        """Check if email exists for creator+campaign"""
        return self.get_email(username, campaign_name) is not None
    
    def get_campaign_emails(self, campaign_name):
        """Get all emails for a specific campaign"""
        emails = []
        for key, data in self.cache.items():
            if data.get('campaign_name') == campaign_name:
                emails.append(data)
        return emails
    
    def clear_campaign_emails(self, campaign_name):
        """Clear all emails for a campaign (useful if campaign brief changes significantly)"""
        keys_to_remove = []
        for key, data in self.cache.items():
            if data.get('campaign_name') == campaign_name:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        if keys_to_remove:
            self.save_cache()
        
        return len(keys_to_remove)