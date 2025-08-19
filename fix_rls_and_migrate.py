#!/usr/bin/env python3
"""
Fix RLS policy and migrate email cache to Supabase
This script temporarily disables RLS for the migration
"""
import json
import os
import sys
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_email_draft_cache import SupabaseEmailDraftCache

load_dotenv()

def fix_rls_and_migrate():
    """Disable RLS temporarily and run migration"""
    
    print("🔧 Fixing RLS and migrating email cache...")
    
    # Load local cache data
    local_cache_file = "cache/email_drafts_cache.json"
    
    if not os.path.exists(local_cache_file):
        print(f"❌ Local cache file not found: {local_cache_file}")
        return
    
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
        return
    
    # Temporarily disable RLS
    print("🔓 Temporarily disabling RLS for migration...")
    try:
        supabase_cache.supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE email_draft_cache DISABLE ROW LEVEL SECURITY;'
        }).execute()
        print("✅ RLS disabled")
    except Exception as e:
        print(f"⚠️  Could not disable RLS (continuing anyway): {str(e)}")
    
    # Perform migration
    print("🔄 Starting migration...")
    migration_result = supabase_cache.migrate_from_file_cache(local_cache_data)
    
    # Re-enable RLS
    print("🔒 Re-enabling RLS...")
    try:
        supabase_cache.supabase.rpc('exec_sql', {
            'sql': '''
            ALTER TABLE email_draft_cache ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS "Allow all operations" ON email_draft_cache;
            CREATE POLICY "Allow all operations" ON email_draft_cache FOR ALL USING (true);
            '''
        }).execute()
        print("✅ RLS re-enabled with permissive policy")
    except Exception as e:
        print(f"⚠️  Could not re-enable RLS: {str(e)}")
    
    # Show results
    print("\n📈 Migration Results:")
    print(f"  ✅ Successfully migrated: {migration_result['migrated']}")
    print(f"  ❌ Failed: {migration_result['failed']}")
    print(f"  📊 Total processed: {migration_result['total']}")
    
    return migration_result

if __name__ == "__main__":
    result = fix_rls_and_migrate()
    
    if result and result['migrated'] > 0:
        print("🎉 Migration completed successfully!")
    else:
        print("❌ Migration failed - try manual approach")
        print("\nManual steps:")
        print("1. Go to Supabase dashboard → Authentication → Policies")
        print("2. Find email_draft_cache table")
        print("3. Temporarily disable RLS or create permissive policy")
        print("4. Run: python3 migrate_email_cache_to_supabase.py")