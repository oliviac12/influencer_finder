#!/usr/bin/env python3
"""
Migration script to transfer email draft cache from local JSON file to Supabase
Run this once to migrate existing cached drafts
"""
import json
import os
import sys
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_email_draft_cache import SupabaseEmailDraftCache

load_dotenv()

def migrate_email_cache():
    """Migrate email drafts from local cache to Supabase"""
    
    # File paths
    local_cache_file = "cache/email_drafts_cache.json"
    
    print("🚀 Starting email draft cache migration to Supabase...")
    
    # Check if local cache file exists
    if not os.path.exists(local_cache_file):
        print(f"❌ Local cache file not found: {local_cache_file}")
        return
    
    # Load local cache data
    try:
        with open(local_cache_file, 'r') as f:
            local_cache_data = json.load(f)
        print(f"📁 Loaded {len(local_cache_data)} drafts from local cache")
    except Exception as e:
        print(f"❌ Error loading local cache file: {str(e)}")
        return
    
    if not local_cache_data:
        print("📭 No drafts found in local cache")
        return
    
    # Initialize Supabase cache
    try:
        supabase_cache = SupabaseEmailDraftCache()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        print("Make sure SUPABASE_URL and SUPABASE_ANON_KEY are set in your environment")
        return
    
    # Show current Supabase cache stats
    current_stats = supabase_cache.get_stats()
    print(f"📊 Current Supabase cache: {current_stats['total_drafts']} drafts")
    
    # Perform migration
    print("\n🔄 Starting migration...")
    migration_result = supabase_cache.migrate_from_file_cache(local_cache_data)
    
    # Show results
    print("\n📈 Migration Results:")
    print(f"  ✅ Successfully migrated: {migration_result['migrated']}")
    print(f"  ❌ Failed: {migration_result['failed']}")
    print(f"  📊 Total processed: {migration_result['total']}")
    
    # Show final stats
    final_stats = supabase_cache.get_stats()
    print(f"\n📊 Final Supabase cache: {final_stats['total_drafts']} drafts")
    
    # Show campaign breakdown
    if final_stats['campaigns']:
        print("\n📋 Campaigns in cache:")
        for campaign, count in final_stats['campaigns'].items():
            print(f"  • {campaign}: {count} drafts")
    
    # Success message
    if migration_result['migrated'] > 0:
        print(f"\n🎉 Migration completed successfully!")
        print(f"📝 Migrated {migration_result['migrated']} email drafts to Supabase")
        
        # Create backup of local cache
        backup_file = f"{local_cache_file}.backup"
        try:
            import shutil
            shutil.copy2(local_cache_file, backup_file)
            print(f"💾 Created backup: {backup_file}")
        except Exception as e:
            print(f"⚠️  Could not create backup: {str(e)}")
    else:
        print("\n⚠️  No drafts were migrated")
    
    return migration_result

def verify_migration():
    """Verify that migration was successful by comparing local and Supabase data"""
    
    local_cache_file = "cache/email_drafts_cache.json"
    
    print("\n🔍 Verifying migration...")
    
    # Load local cache
    try:
        with open(local_cache_file, 'r') as f:
            local_cache_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading local cache: {str(e)}")
        return False
    
    # Initialize Supabase cache
    try:
        supabase_cache = SupabaseEmailDraftCache()
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return False
    
    # Check each draft
    missing_drafts = []
    verified_count = 0
    
    for cache_key, local_draft in local_cache_data.items():
        username = local_draft.get('username')
        campaign = local_draft.get('campaign')
        
        if not username or not campaign:
            print(f"⚠️  Skipping draft with missing username/campaign: {cache_key}")
            continue
        
        # Check if draft exists in Supabase
        supabase_draft = supabase_cache.get_draft(username, campaign)
        if supabase_draft:
            verified_count += 1
            # Verify content matches
            if (supabase_draft.get('subject') != local_draft.get('subject') or
                supabase_draft.get('body') != local_draft.get('body')):
                print(f"⚠️  Content mismatch for {username} in {campaign}")
        else:
            missing_drafts.append(f"{username} ({campaign})")
    
    print(f"✅ Verified {verified_count} drafts in Supabase")
    
    if missing_drafts:
        print(f"❌ Missing {len(missing_drafts)} drafts:")
        for missing in missing_drafts[:10]:  # Show first 10
            print(f"  • {missing}")
        if len(missing_drafts) > 10:
            print(f"  • ... and {len(missing_drafts) - 10} more")
        return False
    else:
        print("🎉 All drafts verified successfully!")
        return True

if __name__ == "__main__":
    # Run migration
    result = migrate_email_cache()
    
    if result and result['migrated'] > 0:
        # Verify migration
        success = verify_migration()
        
        if success:
            print("\n✅ Migration and verification completed successfully!")
            print("\n🔄 Next steps:")
            print("1. Update your email outreach code to use SupabaseEmailDraftCache")
            print("2. Test the Supabase cache functionality")
            print("3. Deploy to ensure persistence across container restarts")
        else:
            print("\n⚠️  Migration completed but verification failed")
            print("Please check the Supabase table manually")
    else:
        print("\n❌ Migration failed or no drafts to migrate")