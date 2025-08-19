"""
Supabase Email Draft Cache Manager
Persistent caching for generated email drafts using Supabase to avoid redundant LLM calls
"""
import os
from datetime import datetime
from typing import Dict, Optional, List
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseEmailDraftCache:
    def __init__(self):
        """Initialize Supabase client for email draft cache"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def get_cache_key(self, username: str, campaign: str, template: str = None) -> str:
        """Generate unique cache key for a draft (for compatibility with file-based cache)"""
        return f"{campaign}_{username}"
    
    def save_draft(self, username: str, campaign: str, template: str = None, 
                   subject: str = None, body: str = None, email: str = None, 
                   personalization: str = None):
        """Save an email draft to Supabase cache"""
        try:
            # Prepare data for upsert
            draft_data = {
                'username': username,
                'campaign': campaign,
                'subject': subject,
                'body': body,
                'email': email,
                'personalization': personalization,
                'generated_at': datetime.now().isoformat(),
                'version': 1
            }
            
            # Use upsert to handle both insert and update cases
            result = self.supabase.table('email_draft_cache').upsert(
                draft_data,
                on_conflict='username,campaign'
            ).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"Error saving draft to Supabase: {str(e)}")
            return None
    
    def get_draft(self, username: str, campaign: str, template: str = None) -> Optional[Dict]:
        """Get cached draft if it exists"""
        try:
            result = self.supabase.table('email_draft_cache').select('*').eq(
                'username', username
            ).eq(
                'campaign', campaign
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error retrieving draft from Supabase: {str(e)}")
            return None
    
    def has_draft(self, username: str, campaign: str, template: str = None) -> bool:
        """Check if draft exists in cache"""
        draft = self.get_draft(username, campaign)
        return draft is not None
    
    def get_campaign_drafts(self, campaign: str) -> List[Dict]:
        """Get all drafts for a campaign"""
        try:
            result = self.supabase.table('email_draft_cache').select('*').eq(
                'campaign', campaign
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error retrieving campaign drafts from Supabase: {str(e)}")
            return []
    
    def clear_campaign_drafts(self, campaign: str):
        """Clear all drafts for a campaign"""
        try:
            # Get count before deletion
            count_result = self.supabase.table('email_draft_cache').select(
                'id', count='exact'
            ).eq('campaign', campaign).execute()
            
            count = count_result.count if count_result.count else 0
            
            # Delete drafts
            result = self.supabase.table('email_draft_cache').delete().eq(
                'campaign', campaign
            ).execute()
            
            return count
            
        except Exception as e:
            print(f"Error clearing campaign drafts from Supabase: {str(e)}")
            return 0
    
    def update_draft_body(self, username: str, campaign: str, new_body: str, template: str = None):
        """Update just the body of a cached draft (for edits)"""
        try:
            result = self.supabase.table('email_draft_cache').update({
                'body': new_body,
                'edited_at': datetime.now().isoformat()
            }).eq(
                'username', username
            ).eq(
                'campaign', campaign
            ).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            print(f"Error updating draft body in Supabase: {str(e)}")
            return False
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            # Get total count
            total_result = self.supabase.table('email_draft_cache').select(
                'id', count='exact'
            ).execute()
            
            total = total_result.count if total_result.count else 0
            
            # Get campaign breakdown
            campaigns_result = self.supabase.table('email_draft_cache').select(
                'campaign'
            ).execute()
            
            campaigns = {}
            if campaigns_result.data:
                for draft in campaigns_result.data:
                    campaign = draft.get('campaign', 'unknown')
                    if campaign not in campaigns:
                        campaigns[campaign] = 0
                    campaigns[campaign] += 1
            
            return {
                'total_drafts': total,
                'campaigns': campaigns,
                'cache_size_kb': 0  # Not applicable for database storage
            }
            
        except Exception as e:
            print(f"Error getting cache stats from Supabase: {str(e)}")
            return {
                'total_drafts': 0,
                'campaigns': {},
                'cache_size_kb': 0
            }
    
    def migrate_from_file_cache(self, file_cache_data: Dict):
        """Migrate data from file-based cache to Supabase"""
        migrated_count = 0
        failed_count = 0
        
        try:
            for cache_key, draft_data in file_cache_data.items():
                # Extract username and campaign from the cache key
                # Format: "{campaign}_{username}"
                if '_' in cache_key:
                    parts = cache_key.split('_', 1)  # Split on first underscore only
                    if len(parts) == 2:
                        campaign, username = parts
                        
                        # Use the existing draft data
                        success = self.save_draft(
                            username=draft_data.get('username', username),
                            campaign=draft_data.get('campaign', campaign),
                            subject=draft_data.get('subject'),
                            body=draft_data.get('body'),
                            email=draft_data.get('email'),
                            personalization=draft_data.get('personalization')
                        )
                        
                        if success:
                            migrated_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            
            return {
                'migrated': migrated_count,
                'failed': failed_count,
                'total': len(file_cache_data)
            }
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return {
                'migrated': migrated_count,
                'failed': failed_count + len(file_cache_data) - migrated_count,
                'total': len(file_cache_data)
            }


# Test the Supabase cache
if __name__ == "__main__":
    try:
        cache = SupabaseEmailDraftCache()
        
        # Test saving a draft
        print("Testing save_draft...")
        result = cache.save_draft(
            username="testcreator",
            campaign="wonder_fall2025",
            subject="Collaboration with Wonder",
            body="Hi there! I love your content...",
            email="test@example.com",
            personalization="I love how you talk about authentic living"
        )
        print(f"Save result: {result}")
        
        # Test retrieving
        print("\nTesting get_draft...")
        draft = cache.get_draft("testcreator", "wonder_fall2025")
        print(f"Retrieved draft: {draft}")
        
        # Test has_draft
        print("\nTesting has_draft...")
        has_draft = cache.has_draft("testcreator", "wonder_fall2025")
        print(f"Has draft: {has_draft}")
        
        # Show stats
        print("\nTesting get_stats...")
        stats = cache.get_stats()
        print(f"Cache stats: {stats}")
        
        # Test campaign drafts
        print("\nTesting get_campaign_drafts...")
        campaign_drafts = cache.get_campaign_drafts("wonder_fall2025")
        print(f"Campaign drafts: {len(campaign_drafts)} found")
        
        # Clean up test data
        print("\nCleaning up test data...")
        cleared = cache.clear_campaign_drafts("wonder_fall2025")
        print(f"Cleared {cleared} test drafts")
        
    except Exception as e:
        print(f"Error testing Supabase cache: {str(e)}")
        print("Make sure SUPABASE_URL and SUPABASE_KEY are set in your environment")