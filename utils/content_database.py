"""
Content Database Manager
Handles saving and loading creator content data (captions, hashtags, etc.)
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional


class ContentDatabase:
    def __init__(self, db_path="cache/creators_content_database.json"):
        self.db_path = db_path
        self.ensure_db_exists()
    
    def ensure_db_exists(self):
        """Create database file if it doesn't exist"""
        if not os.path.exists(self.db_path):
            # Create directory if needed
            dir_path = os.path.dirname(self.db_path)
            if dir_path:  # Only create directory if there is one
                os.makedirs(dir_path, exist_ok=True)
            
            # Initialize empty database
            empty_db = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "creator_count": 0,
                    "total_posts": 0
                },
                "creators": {}
            }
            with open(self.db_path, 'w') as f:
                json.dump(empty_db, f, indent=2)
    
    def load_database(self) -> Dict:
        """Load the entire database"""
        with open(self.db_path, 'r') as f:
            return json.load(f)
    
    def save_database(self, db_data: Dict):
        """Save the entire database"""
        with open(self.db_path, 'w') as f:
            json.dump(db_data, f, indent=2)
    
    def save_creator_content(self, username: str, profile_data: Dict, top_posts_data: List[Dict]):
        """
        Save creator content data to the database
        
        Args:
            username: Creator username (without @)
            profile_data: Profile information 
            top_posts_data: Array of posts with captions/hashtags
        """
        db = self.load_database()
        
        # Extract email from bio
        bio_text = profile_data.get("biography", "") or ""
        email = self._extract_email_from_bio(bio_text)
        
        # Prepare creator data
        creator_content = {
            "profile": {
                "followers": profile_data.get("followers", 0),
                "nickname": profile_data.get("nickname", ""),
                "bio": bio_text,
                "email": email,  # Will be empty string if not found
                "verified": profile_data.get("is_verified", False),
                "language": profile_data.get("predicted_lang", ""),
                "is_commerce": profile_data.get("is_commerce_user", False),
                "last_scraped": datetime.now().isoformat()
            },
            "posts": []
        }
        
        # Process posts data - keep only essential fields for storage efficiency
        for post in top_posts_data:
            post_data = {
                "id": post.get("post_id", ""),
                "desc": post.get("description", "") or "",  # Handle None values
                "tags": post.get("hashtags", []) or [],      # Handle None values
                "date": post.get("create_time", ""),
                "likes": post.get("likes", 0),
                "type": post.get("post_type", "video")
            }
            creator_content["posts"].append(post_data)
        
        # Update database
        db["creators"][username] = creator_content
        
        # Update metadata
        db["metadata"]["last_updated"] = datetime.now().isoformat()
        db["metadata"]["creator_count"] = len(db["creators"])
        db["metadata"]["total_posts"] = sum(len(creator["posts"]) for creator in db["creators"].values())
        
        # Save updated database
        self.save_database(db)
        
        print(f"   💾 Saved content data for @{username}: {len(creator_content['posts'])} posts")
    
    def get_creator_content(self, username: str) -> Optional[Dict]:
        """Get content data for a specific creator"""
        db = self.load_database()
        return db["creators"].get(username)
    
    def update_creator_profile(self, username: str, profile_data: Dict):
        """Update profile data for an existing creator"""
        db = self.load_database()
        if username in db["creators"]:
            db["creators"][username]["profile"] = profile_data
            db["metadata"]["last_updated"] = datetime.now().isoformat()
            self.save_database(db)
            return True
        return False
    
    def creator_exists(self, username: str) -> bool:
        """Check if creator already has content data"""
        db = self.load_database()
        return username in db["creators"]
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        db = self.load_database()
        return db["metadata"]
    
    def search_creators_by_hashtag(self, hashtag: str) -> List[str]:
        """Search creators who use a specific hashtag"""
        db = self.load_database()
        matching_creators = []
        
        for username, data in db["creators"].items():
            for post in data["posts"]:
                if hashtag.lower() in [tag.lower() for tag in post.get("tags", [])]:
                    matching_creators.append(username)
                    break
        
        return matching_creators
    
    def search_creators_by_keyword(self, keyword: str) -> List[str]:
        """Search creators who mention a keyword in captions"""
        db = self.load_database()
        matching_creators = []
        
        keyword_lower = keyword.lower()
        
        for username, data in db["creators"].items():
            for post in data["posts"]:
                desc = post.get("desc", "").lower()
                if keyword_lower in desc:
                    matching_creators.append(username)
                    break
        
        return matching_creators
    
    def _extract_email_from_bio(self, bio_text: str) -> str:
        """
        Extract email address from bio text
        
        Args:
            bio_text: The creator's bio text
            
        Returns:
            Email address if found, empty string otherwise
        """
        if not bio_text:
            return ""
        
        # Common email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Search for email in bio
        matches = re.findall(email_pattern, bio_text)
        
        if matches:
            # Return the first valid email found
            # Filter out common false positives
            for email in matches:
                # Skip if it's just an @ mention
                if not any(char.isdigit() for char in email.split('@')[0]):
                    return email.lower()
            return matches[0].lower() if matches else ""
        
        return ""


# Test the database functionality
if __name__ == "__main__":
    print("🧪 Testing Content Database")
    
    # Initialize database
    db = ContentDatabase("test_content_db.json")
    
    # Test data
    test_profile = {
        "followers": 100000,
        "nickname": "Test Creator",
        "biography": "Test bio",
        "is_verified": False
    }
    
    test_posts = [
        {
            "post_id": "123456",
            "description": "Testing #fashion #style",
            "hashtags": ["fashion", "style"],
            "create_time": "2025-08-02T10:00:00.000Z",
            "likes": 1000
        }
    ]
    
    # Save test data
    db.save_creator_content("testuser", test_profile, test_posts)
    
    # Test retrieval
    creator_data = db.get_creator_content("testuser")
    print(f"Retrieved data: {creator_data}")
    
    # Test search
    fashion_creators = db.search_creators_by_hashtag("fashion")
    print(f"Fashion creators: {fashion_creators}")
    
    # Clean up
    import os
    os.remove("test_content_db.json")
    
    print("✅ Content database test complete!")