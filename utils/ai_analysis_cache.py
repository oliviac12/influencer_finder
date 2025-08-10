"""
AI Analysis Cache Manager
Caches creator analyses to avoid redundant API calls
Implements 7-day expiry for cached analyses
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import hashlib


class AIAnalysisCache:
    def __init__(self, cache_path="cache/ai_analysis_cache.json"):
        self.cache_path = cache_path
        self.cache_duration_days = 7
        self.ensure_cache_exists()
    
    def ensure_cache_exists(self):
        """Create cache file if it doesn't exist"""
        if not os.path.exists(self.cache_path):
            # Create directory if needed
            dir_path = os.path.dirname(self.cache_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Initialize empty cache
            empty_cache = {}
            with open(self.cache_path, 'w') as f:
                json.dump(empty_cache, f, indent=2)
    
    def load_cache(self) -> Dict:
        """Load the entire cache"""
        try:
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_cache(self, cache_data: Dict):
        """Save the entire cache"""
        with open(self.cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def get_cache_key(self, username: str, campaign_brief: str) -> str:
        """Generate a unique cache key for username + campaign combination"""
        # Create hash of campaign brief to handle long briefs
        brief_hash = hashlib.md5(campaign_brief.encode()).hexdigest()[:8]
        return f"{username}_{brief_hash}"
    
    def get_cached_analysis(self, username: str, campaign_brief: str) -> Optional[Dict]:
        """
        Get cached analysis if it exists and is not expired
        
        Args:
            username: Creator username
            campaign_brief: The campaign brief used for analysis
            
        Returns:
            Cached analysis dict if valid, None otherwise
        """
        cache = self.load_cache()
        cache_key = self.get_cache_key(username, campaign_brief)
        
        if cache_key not in cache:
            return None
        
        cached_data = cache[cache_key]
        
        # Check if expired
        cached_time = datetime.fromisoformat(cached_data['analyzed_at'])
        expiry_time = cached_time + timedelta(days=self.cache_duration_days)
        
        if datetime.now() > expiry_time:
            # Expired - remove from cache
            del cache[cache_key]
            self.save_cache(cache)
            return None
        
        return cached_data
    
    def save_analysis(self, username: str, campaign_brief: str, analysis: str, recommendation: str = ""):
        """
        Save analysis to cache
        
        Args:
            username: Creator username
            campaign_brief: The campaign brief used
            analysis: The AI analysis text
            recommendation: Extracted recommendation (Yes/No/Maybe)
        """
        cache = self.load_cache()
        cache_key = self.get_cache_key(username, campaign_brief)
        
        cache[cache_key] = {
            'username': username,
            'campaign_brief': campaign_brief,
            'analysis': analysis,
            'recommendation': recommendation,
            'analyzed_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=self.cache_duration_days)).isoformat()
        }
        
        self.save_cache(cache)
    
    def get_all_analyses_for_creator(self, username: str) -> List[Dict]:
        """Get all cached analyses for a specific creator"""
        cache = self.load_cache()
        creator_analyses = []
        
        for key, data in cache.items():
            if data.get('username') == username:
                # Check if expired
                expiry = datetime.fromisoformat(data['expires_at'])
                if datetime.now() <= expiry:
                    creator_analyses.append(data)
        
        return creator_analyses
    
    def clear_expired_entries(self):
        """Remove all expired entries from cache"""
        cache = self.load_cache()
        current_time = datetime.now()
        
        # Find expired entries
        expired_keys = []
        for key, data in cache.items():
            expiry = datetime.fromisoformat(data['expires_at'])
            if current_time > expiry:
                expired_keys.append(key)
        
        # Remove expired entries
        for key in expired_keys:
            del cache[key]
        
        if expired_keys:
            self.save_cache(cache)
            
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache"""
        cache = self.load_cache()
        current_time = datetime.now()
        
        total_entries = len(cache)
        expired_count = 0
        unique_creators = set()
        unique_campaigns = set()
        
        for data in cache.values():
            unique_creators.add(data.get('username'))
            unique_campaigns.add(data.get('campaign_brief'))
            
            expiry = datetime.fromisoformat(data['expires_at'])
            if current_time > expiry:
                expired_count += 1
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_count,
            'expired_entries': expired_count,
            'unique_creators': len(unique_creators),
            'unique_campaigns': len(unique_campaigns),
            'cache_size_kb': os.path.getsize(self.cache_path) / 1024 if os.path.exists(self.cache_path) else 0
        }


# Test the cache functionality
if __name__ == "__main__":
    print("🧪 Testing AI Analysis Cache")
    
    cache = AIAnalysisCache()
    
    # Test saving analysis
    test_analysis = """
    **Why is this creator a good match?**
    They create fashion and lifestyle content that aligns perfectly with the campaign.
    
    **What topics does this creator talk about?**
    Fashion, travel, lifestyle, beauty products.
    
    **Overall Recommendation: Yes**
    """
    
    cache.save_analysis(
        username="testcreator",
        campaign_brief="fashion and lifestyle brand collaboration",
        analysis=test_analysis,
        recommendation="Yes"
    )
    
    # Test retrieving
    cached = cache.get_cached_analysis("testcreator", "fashion and lifestyle brand collaboration")
    if cached:
        print("✅ Cache save/retrieve working")
        print(f"   Expires at: {cached['expires_at']}")
    
    # Test stats
    stats = cache.get_cache_stats()
    print(f"\n📊 Cache stats: {stats}")
    
    print("\n✅ AI Analysis Cache system ready!")