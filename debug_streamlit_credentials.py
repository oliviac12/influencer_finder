#!/usr/bin/env python3
"""
Debug Streamlit Cloud Credential Access
Test how EmailOutreachManager accesses Supabase credentials vs other components
"""
import os
import sys

# Add app directory to path
sys.path.append('app')
sys.path.append('utils')

def test_environment_variables():
    """Test direct environment variable access"""
    print("🔍 Testing Environment Variables:")
    print("=" * 50)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"SUPABASE_URL: {'SET' if supabase_url else 'NOT SET'}")
    print(f"SUPABASE_KEY: {'SET' if supabase_key else 'NOT SET'}")
    
    if supabase_url:
        print(f"URL length: {len(supabase_url)}")
    if supabase_key:
        print(f"Key length: {len(supabase_key)}")
    
    return supabase_url, supabase_key

def test_supabase_cache_direct():
    """Test SupabaseEmailDraftCache (working method)"""
    print("\n📊 Testing SupabaseEmailDraftCache (Working):")
    print("=" * 50)
    
    try:
        from supabase_email_draft_cache import SupabaseEmailDraftCache
        cache = SupabaseEmailDraftCache()
        stats = cache.get_stats()
        print(f"✅ SUCCESS: {stats['total_drafts']} drafts found")
        print(f"Campaigns: {list(stats['campaigns'].keys())}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_email_outreach_manager():
    """Test EmailOutreachManager (problematic method)"""
    print("\n📧 Testing EmailOutreachManager (Problematic):")
    print("=" * 50)
    
    try:
        from email_outreach_v2 import EmailOutreachManager
        manager = EmailOutreachManager()
        
        print(f"Cache status: {manager.cache_status}")
        print(f"Using Supabase: {manager.use_supabase}")
        print(f"Supabase client available: {manager.supabase is not None}")
        
        if hasattr(manager, 'debug_info'):
            print("\nDebug info:")
            for key, value in manager.debug_info.items():
                print(f"  {key}: {value}")
        
        # Test if we can access cache
        if manager.use_supabase and hasattr(manager.draft_cache, 'get_stats'):
            stats = manager.draft_cache.get_stats()
            print(f"✅ Cache access works: {stats['total_drafts']} drafts")
        else:
            print("❌ Cache access not available")
            
        return manager.use_supabase
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_streamlit_secrets_simulation():
    """Simulate Streamlit secrets access"""
    print("\n🔄 Simulating Streamlit Secrets:")
    print("=" * 50)
    
    # Clear environment variables to simulate Streamlit Cloud
    original_url = os.getenv('SUPABASE_URL')
    original_key = os.getenv('SUPABASE_KEY')
    
    # Remove env vars
    if 'SUPABASE_URL' in os.environ:
        del os.environ['SUPABASE_URL']
    if 'SUPABASE_KEY' in os.environ:
        del os.environ['SUPABASE_KEY']
    
    print("Environment variables cleared")
    print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')}")
    print(f"SUPABASE_KEY: {os.getenv('SUPABASE_KEY', 'NOT SET')}")
    
    # Now test EmailOutreachManager
    try:
        # Clear module cache to force re-import
        if 'email_outreach_v2' in sys.modules:
            del sys.modules['email_outreach_v2']
        
        from email_outreach_v2 import EmailOutreachManager
        manager = EmailOutreachManager()
        print(f"\\nResult with no env vars:")
        print(f"Cache status: {manager.cache_status}")
        print(f"Using Supabase: {manager.use_supabase}")
        
    except Exception as e:
        print(f"Error testing without env vars: {e}")
    
    # Restore original values
    if original_url:
        os.environ['SUPABASE_URL'] = original_url
    if original_key:
        os.environ['SUPABASE_KEY'] = original_key

def main():
    print("🚀 Streamlit Cloud Credential Debug Tool")
    print("=" * 60)
    
    # Test 1: Environment variables
    url, key = test_environment_variables()
    
    # Test 2: Direct cache (working)
    cache_works = test_supabase_cache_direct()
    
    # Test 3: EmailOutreachManager (problematic)
    manager_works = test_email_outreach_manager()
    
    # Test 4: Simulate Streamlit Cloud environment
    test_streamlit_secrets_simulation()
    
    print("\n📊 Summary:")
    print("=" * 30)
    print(f"Environment variables: {'✅' if url and key else '❌'}")
    print(f"SupabaseEmailDraftCache: {'✅' if cache_works else '❌'}")
    print(f"EmailOutreachManager: {'✅' if manager_works else '❌'}")
    
    if cache_works and not manager_works:
        print("\n🔍 DIAGNOSIS: EmailOutreachManager credential logic has a bug")
        print("The credentials work for SupabaseEmailDraftCache but not EmailOutreachManager")

if __name__ == "__main__":
    main()