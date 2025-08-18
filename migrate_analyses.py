#!/usr/bin/env python3
"""
Migration script to move AI analyses from creator_reviews.json to ai_analysis_cache.json
"""
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.ai_analysis_cache import AIAnalysisCache

def migrate_analyses():
    """Migrate analyses from creator_reviews.json to AI cache"""
    
    # Load creator reviews
    reviews_file = "creator_reviews.json"
    if not os.path.exists(reviews_file):
        print(f"❌ {reviews_file} not found")
        return
    
    with open(reviews_file, 'r') as f:
        reviews = json.load(f)
    
    print(f"📁 Found {len(reviews)} entries in creator_reviews.json")
    
    # Initialize AI cache
    ai_cache = AIAnalysisCache()
    
    migrated_count = 0
    skipped_count = 0
    
    for username, review_data in reviews.items():
        # Extract required fields
        analysis = review_data.get('analysis', '')
        campaign_brief = review_data.get('campaign_brief', '')
        recommendation = review_data.get('recommendation', 'Maybe')
        
        if not analysis or not campaign_brief:
            print(f"⚠️  Skipping {username}: missing analysis or campaign_brief")
            skipped_count += 1
            continue
        
        # Determine campaign name from the brief
        # Both campaigns have similar briefs, let's map based on timing or default to wonder_fall2025
        campaign_name = "wonder_fall2025"  # Default
        
        # Check if this analysis already exists in cache
        existing = ai_cache.get_cached_analysis(username, campaign_name)
        if existing:
            print(f"✅ {username} already in cache, skipping")
            skipped_count += 1
            continue
        
        # Normalize recommendation format
        if recommendation.lower() in ['recommended', 'yes']:
            recommendation = 'Yes'
        elif recommendation.lower() in ['not recommended', 'no']:
            recommendation = 'No'
        else:
            recommendation = 'Maybe'
        
        try:
            # Save to AI cache
            ai_cache.save_analysis(
                username=username,
                campaign_name=campaign_name,
                campaign_brief=campaign_brief.strip(),
                analysis=analysis,
                recommendation=recommendation
            )
            print(f"✅ Migrated {username} to AI cache")
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Failed to migrate {username}: {e}")
            skipped_count += 1
    
    print(f"\n📊 Migration complete:")
    print(f"   ✅ Migrated: {migrated_count}")
    print(f"   ⚠️  Skipped: {skipped_count}")
    print(f"   📁 Total: {len(reviews)}")
    
    # Show cache stats
    cache_data = ai_cache.load_cache()
    print(f"\n💾 AI cache now has {len(cache_data)} total entries")

if __name__ == "__main__":
    migrate_analyses()