"""
Simplified Shoppable Content Filter - Only checks for isECVideo indicator
"""
import requests
import time
import re
import json


class ShoppableContentFilter:
    def __init__(self):
        pass
    
    def check_tiktok_commission_eligible(self, tiktok_url: str) -> bool:
        """
        Check TikTok video for isECVideo indicator only
        
        Args:
            tiktok_url: TikTok video URL
            
        Returns:
            bool: True if isECVideo == 1, False otherwise
        """
        try:
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(tiktok_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            
            # Check TikTok's JSON data for isECVideo only
            return self._parse_tiktok_json_for_commerce(html_content)
            
        except Exception as e:
            print(f"Warning: Could not check commission eligibility for {tiktok_url}: {e}")
            return False
    
    def _parse_tiktok_json_for_commerce(self, html_content: str) -> bool:
        """
        Parse TikTok's embedded JSON data for isECVideo indicator only
        
        Returns:
            bool: True if isECVideo == 1, False otherwise
        """
        try:
            # Extract the main data structure
            match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>', html_content, re.DOTALL)
            if not match:
                return False
            
            data = json.loads(match.group(1))
            
            # Navigate to video item data
            item_struct = data.get('__DEFAULT_SCOPE__', {}).get('webapp.video-detail', {}).get('itemInfo', {}).get('itemStruct', {})
            if not item_struct:
                return False
            
            # Check for isECVideo (primary indicator)
            if item_struct.get('isECVideo', 0) == 1:
                return True
            
            # Check for product anchors (TikTok Shop integration)
            anchors = item_struct.get('anchors', [])
            for anchor in anchors:
                if anchor.get('type') == 35:  # Product anchor type
                    return True
            
            return False
            
        except Exception as e:
            print(f"   Warning: JSON parsing failed: {e}")
            return False