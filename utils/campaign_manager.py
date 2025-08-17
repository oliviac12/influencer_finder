"""
Campaign Manager
Stores campaign names and their associated briefs
"""
import json
import os
from datetime import datetime

class CampaignManager:
    def __init__(self, cache_file="cache/campaigns.json"):
        self.cache_file = cache_file
        self.campaigns = self.load_campaigns()
    
    def load_campaigns(self):
        """Load existing campaigns from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_campaigns(self):
        """Save campaigns to file"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.campaigns, f, indent=2)
    
    def save_campaign(self, campaign_name, campaign_brief):
        """Save or update a campaign and its brief"""
        self.campaigns[campaign_name] = {
            'name': campaign_name,
            'brief': campaign_brief,
            'updated_at': datetime.now().isoformat()
        }
        self.save_campaigns()
    
    def get_campaign_brief(self, campaign_name):
        """Get the brief for a campaign"""
        campaign = self.campaigns.get(campaign_name, {})
        return campaign.get('brief', '')
    
    def get_all_campaign_names(self):
        """Get list of all campaign names"""
        return list(self.campaigns.keys())
    
    def campaign_exists(self, campaign_name):
        """Check if a campaign exists"""
        return campaign_name in self.campaigns