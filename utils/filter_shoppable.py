"""
Simplified Shoppable Content Filter - Only checks for isECVideo indicator
Optimized with batch processing for better performance
"""
import requests
import time
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict


class ShoppableContentFilter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
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
            time.sleep(0.5)  # Reduced delay for single requests
            
            response = self.session.get(tiktok_url, timeout=10)
            response.raise_for_status()
            
            html_content = response.text
            
            # Check TikTok's JSON data for isECVideo only
            return self._parse_tiktok_json_for_commerce(html_content)
            
        except Exception as e:
            print(f"Warning: Could not check commission eligibility for {tiktok_url}: {e}")
            return False
    
    def check_batch_tiktok_commission_eligible(self, tiktok_urls: List[str]) -> Dict[str, bool]:
        """
        Check multiple TikTok videos for shoppable content in parallel
        
        Args:
            tiktok_urls: List of TikTok video URLs
            
        Returns:
            Dict mapping URL to shoppable status (True/False)
        """
        if not tiktok_urls:
            return {}
        
        results = {}
        
        # Use parallel processing for batch checking
        with ThreadPoolExecutor(max_workers=3) as executor:  # Conservative thread count
            # Submit all URL checks
            future_to_url = {
                executor.submit(self._check_single_url, url): url 
                for url in tiktok_urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    print(f"Warning: Batch check failed for {url}: {e}")
                    results[url] = False
        
        return results
    
    def _check_single_url(self, tiktok_url: str) -> bool:
        """
        Internal method for checking a single URL (used in batch processing)
        """
        try:
            # Shorter delay for batch processing
            time.sleep(0.2)
            
            response = self.session.get(tiktok_url, timeout=8)
            response.raise_for_status()
            
            return self._parse_tiktok_json_for_commerce(response.text)
            
        except Exception:
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