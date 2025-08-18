"""
Email Draft Cache Manager
Persistent caching for generated email drafts to avoid redundant LLM calls
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, List


class EmailDraftCache:
    def __init__(self, cache_file="cache/email_drafts_cache.json"):
        self.cache_file = cache_file
        self.cache = self.load_cache()
    
    def load_cache(self) -> dict:
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
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_cache_key(self, username: str, campaign: str, template: str = None) -> str:
        """Generate unique cache key for a draft"""
        return f"{campaign}_{username}"
    
    def save_draft(self, username: str, campaign: str, template: str = None, 
                   subject: str = None, body: str = None, email: str = None, 
                   personalization: str = None):
        """Save an email draft to cache"""
        cache_key = self.get_cache_key(username, campaign)
        
        self.cache[cache_key] = {
            'username': username,
            'campaign': campaign,
            'subject': subject,
            'body': body,
            'email': email,
            'personalization': personalization,
            'generated_at': datetime.now().isoformat(),
            'version': 1  # For future schema changes
        }
        
        self.save_cache()
    
    def get_draft(self, username: str, campaign: str, template: str = None) -> Optional[Dict]:
        """Get cached draft if it exists"""
        cache_key = self.get_cache_key(username, campaign)
        return self.cache.get(cache_key)
    
    def has_draft(self, username: str, campaign: str, template: str = None) -> bool:
        """Check if draft exists in cache"""
        cache_key = self.get_cache_key(username, campaign)
        return cache_key in self.cache
    
    def get_campaign_drafts(self, campaign: str) -> List[Dict]:
        """Get all drafts for a campaign"""
        drafts = []
        for key, draft in self.cache.items():
            if draft.get('campaign') == campaign:
                drafts.append(draft)
        return drafts
    
    def clear_campaign_drafts(self, campaign: str):
        """Clear all drafts for a campaign"""
        keys_to_remove = []
        for key, draft in self.cache.items():
            if draft.get('campaign') == campaign:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
        
        self.save_cache()
        return len(keys_to_remove)
    
    def update_draft_body(self, username: str, campaign: str, new_body: str, template: str = None):
        """Update just the body of a cached draft (for edits)"""
        cache_key = self.get_cache_key(username, campaign)
        if cache_key in self.cache:
            self.cache[cache_key]['body'] = new_body
            self.cache[cache_key]['edited_at'] = datetime.now().isoformat()
            self.save_cache()
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        campaigns = {}
        total = len(self.cache)
        
        for draft in self.cache.values():
            campaign = draft.get('campaign', 'unknown')
            if campaign not in campaigns:
                campaigns[campaign] = 0
            campaigns[campaign] += 1
        
        return {
            'total_drafts': total,
            'campaigns': campaigns,
            'cache_size_kb': os.path.getsize(self.cache_file) / 1024 if os.path.exists(self.cache_file) else 0
        }


# Test the cache
if __name__ == "__main__":
    cache = EmailDraftCache()
    
    # Test saving a draft
    cache.save_draft(
        username="testcreator",
        campaign="wonder_fall2025",
        subject="Collaboration with Wonder",
        body="Hi there! I love your content...",
        email="test@example.com",
        personalization="I love how you talk about authentic living"
    )
    
    # Test retrieving
    draft = cache.get_draft("testcreator", "wonder_fall2025")
    print(f"Retrieved draft: {draft}")
    
    # Show stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")