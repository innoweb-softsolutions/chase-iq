import logging
import time
import re
from datetime import datetime

import facebook_scraper as fb_scraper
from ..utils.helpers import safe_request
from ..config import DELAY_BETWEEN_REQUESTS

logger = logging.getLogger(__name__)

class ProfileExtractor:
    """Extract profile data from Facebook users."""
    
    def __init__(self, delay=DELAY_BETWEEN_REQUESTS):
        """Initialize the extractor."""
        self.delay = delay
        
    def extract_profile(self, username, cookies=None):
        """Extract profile information for a Facebook user."""
        logger.info(f"Extracting profile data for: {username}")
        
        try:
            profile = safe_request(fb_scraper.get_profile, 
                                username, 
                                cookies=cookies)
            
            # Extract relevant information
            result = {
                'username': username,
                'name': profile.get('Name', 'N/A'),
                'user_id': profile.get('id', 'N/A'),
                'profile_url': f"https://facebook.com/{username}",
                'about': profile.get('About', ''),
                'work': self._parse_work_experience(profile.get('Work', '')),
                'education': profile.get('Education', ''),
                'places_lived': profile.get('Places lived', []),
                'profile_picture': profile.get('profile_picture'),
            }
            
            logger.info(f"Successfully extracted profile for {username}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting profile for {username}: {e}")
            return None
    
    def _parse_work_experience(self, work_text):
        """Parse work experience from profile text."""
        if not work_text:
            return []
            
        work_experiences = []
        entries = work_text.split('\n\n')
        
        current_entry = {}
        for entry in entries:
            lines = entry.split('\n')
            if len(lines) >= 2:
                company = lines[0]
                title = lines[1]
                
                date_range = None
                location = None
                
                if len(lines) >= 3:
                    # Try to parse date range
                    date_match = re.search(r'(\w+ \d{4}) - (Present|\w+ \d{4})', lines[2])
                    if date_match:
                        date_range = lines[2]
                        
                if len(lines) >= 4:
                    # Last line might be location
                    location = lines[3]
                
                work_experiences.append({
                    'company': company,
                    'title': title,
                    'date_range': date_range,
                    'location': location
                })
        
        return work_experiences
        
    def extract_profiles_from_posts(self, posts, cookies=None):
        """Extract profiles from a list of posts."""
        profiles = []
        processed_users = set()
        
        for post in posts:
            username = post.get('username')
            
            # Skip if username is missing or already processed
            if not username or username in processed_users:
                continue
                
            profile = self.extract_profile(username, cookies)
            if profile:
                profiles.append(profile)
                processed_users.add(username)
                
            # Respect rate limits
            time.sleep(self.delay)
            
        logger.info(f"Extracted {len(profiles)} profiles from posts")
        return profiles