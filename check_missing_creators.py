#!/usr/bin/env python3
"""
Quick script to check for missing creators in the database
"""
import pandas as pd
import json
import os
from utils.content_database import ContentDatabase


def check_missing_creators():
    """Find creators in CSV files that are missing from database"""
    # Get all creators from CSV files
    all_csv_creators = set()
    input_dir = "data/inputs/"
    
    print("📁 Checking CSV files...")
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv'):
            csv_path = os.path.join(input_dir, filename)
            try:
                df = pd.read_csv(csv_path)
                username_cols = [col for col in df.columns if 'username' in col.lower()]
                if username_cols:
                    usernames = df[username_cols[0]].dropna().unique()
                    all_csv_creators.update(usernames)
                    print(f"   {filename}: {len(usernames)} creators")
            except Exception as e:
                print(f"   Error reading {filename}: {e}")
    
    # Get creators in database
    content_db = ContentDatabase()
    db = content_db.load_database()
    db_creators = set(db.get('creators', {}).keys())
    
    # Find missing
    missing_creators = all_csv_creators - db_creators
    
    print(f"\n📊 Summary:")
    print(f"   Total in CSVs: {len(all_csv_creators)}")
    print(f"   Total in database: {len(db_creators)}")
    print(f"   Missing: {len(missing_creators)}")
    print(f"   Completion: {len(db_creators)/len(all_csv_creators)*100:.1f}%")
    
    if missing_creators:
        print(f"\n❌ Sample missing creators (first 20):")
        for i, creator in enumerate(sorted(list(missing_creators))[:20], 1):
            print(f"   {i}. @{creator}")
        
        # Check specific creator
        if 'astoldbyanisa' in missing_creators:
            print(f"\n🎯 'astoldbyanisa' is MISSING from database")
        else:
            print(f"\n✅ 'astoldbyanisa' is in database")
    else:
        print("\n✅ All creators have been processed!")
    
    return missing_creators


if __name__ == "__main__":
    missing = check_missing_creators()
    
    if missing and len(missing) > 20:
        print(f"\n💡 Run 'python backfill_retry_missing.py' to process {len(missing)} missing creators")