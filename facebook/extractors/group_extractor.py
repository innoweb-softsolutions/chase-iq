import logging
import time
from datetime import datetime

import facebook_scraper as fb_scraper
from ..utils.helpers import safe_request
from ..config import POSTS_PER_PAGE, DELAY_BETWEEN_REQUESTS

logger = logging.getLogger(__name__)

class GroupExtractor:
    """Extract data from Facebook groups."""
    
    def __init__(self, max_posts=50, max_pages=10, delay=DELAY_BETWEEN_REQUESTS):
        """Initialize the extractor."""
        self.max_posts = max_posts
        self.max_pages = max_pages
        self.delay = delay
        
    def _scrape_group_with_http(self, group_id, cookies=None):
        """Scrape a Facebook group using the HTTP-based approach."""
        logger.info(f"Scraping Facebook group: {group_id}")
        
        posts = []
        options = {"posts_per_page": POSTS_PER_PAGE}
        
        # If cookies is a dict with email/pass, use credentials instead
        if isinstance(cookies, dict) and "email" in cookies and "pass" in cookies:
            options["credentials"] = (cookies["email"], cookies["pass"])
            cookies = None
            
        try:
            post_generator = fb_scraper.get_posts(
                group=group_id,
                pages=self.max_pages,
                options=options,
                cookies=cookies
            )
            
            for post in post_generator:
                if len(posts) >= self.max_posts:
                    break
                    
                # Skip posts without text
                if not post.get('text'):
                    continue
                    
                posts.append(post)
                logger.debug(f"Retrieved post ID: {post.get('post_id')}")
                time.sleep(self.delay)
                
        except Exception as e:
            logger.error(f"Error scraping group {group_id}: {e}")
            
        logger.info(f"Retrieved {len(posts)} posts from group {group_id}")
        return posts
        
    def _scrape_group_with_selenium(self, group_id, email=None, password=None):
        """Fallback method to scrape a Facebook group using Selenium."""
        # This is a fallback implementation using the Selenium-based scraper
        try:
            # Import the Selenium-based scraper only when needed
            from facebook_page_scraper import Facebook_scraper
            
            logger.info(f"Attempting fallback scraping of group {group_id} with Selenium")
            
            # Initialize the scraper
            scraper = Facebook_scraper(
                group_id, 
                self.max_posts, 
                "chrome", 
                headless=True, 
                isGroup=True,
                username=email,
                password=password
            )
            
            # Get the data as JSON
            json_data = scraper.scrap_to_json()
            
            # Convert to the expected format
            import json
            data = json.loads(json_data)
            
            posts = []
            for post_id, post_data in data.items():
                post = {
                    'post_id': post_id,
                    'username': post_data.get('name', 'N/A'),
                    'text': post_data.get('content', ''),
                    'time': post_data.get('posted_on'),
                    'link': None,
                    'post_url': post_data.get('post_url'),
                    'image': post_data.get('image', [])[0] if post_data.get('image') else None,
                    'images': post_data.get('image', []),
                    'comments': post_data.get('comments', 0),
                    'shares': post_data.get('shares', 0),
                    'likes': post_data.get('reactions', {}).get('likes', 0) if post_data.get('reactions') else 0,
                }
                posts.append(post)
                
            logger.info(f"Retrieved {len(posts)} posts from group {group_id} using Selenium")
            return posts
            
        except Exception as e:
            logger.error(f"Selenium fallback also failed for group {group_id}: {e}")
            return []
    
    def scrape_group(self, group_id, use_selenium_fallback=False, email=None, password=None, cookies=None):
        """Main method to scrape a Facebook group."""
        posts = self._scrape_group_with_http(group_id, cookies)
        
        # If HTTP-based approach failed or returned no results, try Selenium as fallback
        if not posts and use_selenium_fallback:
            # Wait a bit before trying the fallback to avoid rate limiting
            time.sleep(self.delay * 2)
            posts = self._scrape_group_with_selenium(group_id, email, password)
            
        return posts