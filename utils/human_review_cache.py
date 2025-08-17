"""
Human Review Cache System
Stores human review decisions by campaign and creator
"""
import json
import os
from datetime import datetime
from pathlib import Path

class HumanReviewCache:
    def __init__(self, cache_file="cache/human_review_cache.json"):
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
    
    def get_review_key(self, username, campaign_name):
        """Generate cache key for creator+campaign"""
        return f"{username}_{campaign_name.lower().replace(' ', '_')}"
    
    def save_review(self, username, campaign_name, decision, notes=""):
        """Save human review decision"""
        key = self.get_review_key(username, campaign_name)
        
        self.cache[key] = {
            'username': username,
            'campaign_name': campaign_name,
            'decision': decision,  # 'approved', 'rejected', 'maybe'
            'notes': notes,
            'reviewed_at': datetime.now().isoformat(),
            'reviewer': os.getenv('USER', 'unknown')
        }
        
        self.save_cache()
    
    def get_review(self, username, campaign_name):
        """Get review decision for creator+campaign"""
        key = self.get_review_key(username, campaign_name)
        return self.cache.get(key)
    
    def has_been_reviewed(self, username, campaign_name):
        """Check if creator has been reviewed for this campaign"""
        return self.get_review(username, campaign_name) is not None
    
    def get_campaign_reviews(self, campaign_name):
        """Get all reviews for a specific campaign"""
        reviews = []
        for key, review in self.cache.items():
            if review.get('campaign_name') == campaign_name:
                reviews.append(review)
        return reviews
    
    def get_campaign_stats(self, campaign_name):
        """Get statistics for a campaign"""
        reviews = self.get_campaign_reviews(campaign_name)
        
        stats = {
            'total_reviewed': len(reviews),
            'approved': sum(1 for r in reviews if r['decision'] == 'approved'),
            'rejected': sum(1 for r in reviews if r['decision'] == 'rejected'),
            'maybe': sum(1 for r in reviews if r['decision'] == 'maybe')
        }
        
        return stats
    
    def update_review(self, username, campaign_name, decision, notes=""):
        """Update an existing review (alias for save_review)"""
        self.save_review(username, campaign_name, decision, notes)