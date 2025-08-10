#!/usr/bin/env python3
"""
Check which creators have extractable emails in their bios
"""
import json
import re
from utils.content_database import ContentDatabase


def check_creator_emails():
    """Check how many creators have emails in their bios"""
    db = ContentDatabase()
    data = db.load_database()
    creators = data.get('creators', {})
    
    creators_with_email = []
    creators_without_email = []
    
    for username, creator_data in creators.items():
        profile = creator_data.get('profile', {})
        bio = profile.get('bio', '')
        existing_email = profile.get('email', '')
        
        # If email not already extracted, try to extract it
        if not existing_email and bio:
            email = db._extract_email_from_bio(bio)
            if email:
                creators_with_email.append((username, email, bio[:100]))
        elif existing_email:
            creators_with_email.append((username, existing_email, bio[:100]))
        else:
            creators_without_email.append(username)
    
    print(f"📊 Email Extraction Summary:")
    print(f"   Total creators: {len(creators)}")
    print(f"   With emails: {len(creators_with_email)} ({len(creators_with_email)/len(creators)*100:.1f}%)")
    print(f"   Without emails: {len(creators_without_email)} ({len(creators_without_email)/len(creators)*100:.1f}%)")
    
    if creators_with_email:
        print(f"\n✅ Sample creators with emails:")
        for username, email, bio_snippet in creators_with_email[:10]:
            print(f"   @{username}: {email}")
            print(f"      Bio: {bio_snippet}...")
    
    return creators_with_email, creators_without_email


if __name__ == "__main__":
    with_email, without_email = check_creator_emails()
    
    print(f"\n💡 For outreach:")
    print(f"   - {len(with_email)} creators can be contacted immediately")
    print(f"   - {len(without_email)} creators need manual email entry")