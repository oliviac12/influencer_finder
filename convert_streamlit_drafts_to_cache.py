#!/usr/bin/env python3
"""
Convert Streamlit Cloud email drafts to cache format for Supabase migration
Takes the downloaded JSON from Streamlit and converts it to the cache format
"""
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.supabase_email_draft_cache import SupabaseEmailDraftCache

load_dotenv()

def convert_streamlit_drafts_to_cache_format(drafts_json_file, campaign_name):
    """Convert Streamlit drafts JSON to cache format"""
    
    print(f"🔄 Converting Streamlit drafts to cache format...")
    print(f"📁 Input file: {drafts_json_file}")
    print(f"📋 Campaign: {campaign_name}")
    
    # Load the downloaded drafts
    try:
        with open(drafts_json_file, 'r') as f:
            drafts = json.load(f)
        print(f"📊 Loaded {len(drafts)} drafts from Streamlit export")
    except Exception as e:
        print(f"❌ Error loading drafts file: {str(e)}")
        return None
    
    # Convert to cache format
    cache_data = {}
    converted_count = 0
    
    for draft in drafts:
        try:
            username = draft.get('username')
            if not username:
                print(f"⚠️  Skipping draft without username")
                continue
            
            # Create cache key
            cache_key = f"{campaign_name}_{username}"
            
            # Convert to cache format
            cache_entry = {
                'username': username,
                'campaign': campaign_name,
                'subject': draft.get('subject'),
                'body': draft.get('body'),
                'email': draft.get('email', draft.get('to_email')),
                'personalization': draft.get('personalization'),
                'generated_at': datetime.now().isoformat(),
                'version': 1
            }
            
            cache_data[cache_key] = cache_entry
            converted_count += 1
            
        except Exception as e:
            print(f"⚠️  Error converting draft for {draft.get('username', 'unknown')}: {str(e)}")
    
    print(f"✅ Converted {converted_count} drafts to cache format")
    
    # Save converted cache data
    cache_file = f"streamlit_cache_export_{campaign_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"💾 Saved cache data to: {cache_file}")
    except Exception as e:
        print(f"❌ Error saving cache file: {str(e)}")
        return None
    
    return cache_data, cache_file

def migrate_to_supabase(cache_data):
    """Migrate cache data directly to Supabase"""
    
    print("\n🚀 Migrating to Supabase...")
    
    try:
        supabase_cache = SupabaseEmailDraftCache()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {str(e)}")
        return False
    
    # Check current Supabase cache
    current_stats = supabase_cache.get_stats()
    print(f"📊 Current Supabase cache: {current_stats['total_drafts']} drafts")
    
    # Perform migration
    migration_result = supabase_cache.migrate_from_file_cache(cache_data)
    
    print("\n📈 Migration Results:")
    print(f"  ✅ Successfully migrated: {migration_result['migrated']}")
    print(f"  ❌ Failed: {migration_result['failed']}")
    print(f"  📊 Total processed: {migration_result['total']}")
    
    # Final stats
    final_stats = supabase_cache.get_stats()
    print(f"\n📊 Final Supabase cache: {final_stats['total_drafts']} drafts")
    
    if final_stats['campaigns']:
        print("\n📋 Campaigns in cache:")
        for campaign, count in final_stats['campaigns'].items():
            print(f"  • {campaign}: {count} drafts")
    
    return migration_result['migrated'] > 0

def main():
    """Main conversion and migration process"""
    
    print("🚀 Streamlit Cloud Drafts Recovery Tool")
    print("=" * 50)
    
    # Get input parameters
    if len(sys.argv) < 2:
        print("Usage: python3 convert_streamlit_drafts_to_cache.py <drafts_json_file> [campaign_name]")
        print("\nExample:")
        print("  python3 convert_streamlit_drafts_to_cache.py streamlit_drafts.json wonder_fall2025_nonshop")
        return
    
    drafts_file = sys.argv[1]
    campaign_name = sys.argv[2] if len(sys.argv) > 2 else "wonder_fall2025_nonshop"
    
    if not os.path.exists(drafts_file):
        print(f"❌ File not found: {drafts_file}")
        return
    
    # Convert drafts to cache format
    result = convert_streamlit_drafts_to_cache_format(drafts_file, campaign_name)
    if not result:
        print("❌ Conversion failed")
        return
    
    cache_data, cache_file = result
    
    # Ask if user wants to migrate to Supabase
    print(f"\n📋 Converted {len(cache_data)} drafts for campaign '{campaign_name}'")
    
    migrate = input("\n🚀 Migrate to Supabase now? (y/n): ").lower().strip()
    
    if migrate == 'y' or migrate == 'yes':
        success = migrate_to_supabase(cache_data)
        if success:
            print("\n🎉 Recovery completed successfully!")
            print("Your Streamlit Cloud drafts are now safely stored in Supabase")
        else:
            print("\n⚠️  Migration had issues - check the output above")
    else:
        print(f"\n💾 Cache data saved to: {cache_file}")
        print("You can migrate later using: python3 migrate_email_cache_to_supabase.py")
    
    print("\n✅ Process complete!")

if __name__ == "__main__":
    main()