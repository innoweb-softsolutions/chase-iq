import logging
import time
import traceback
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
            logger.debug("Using email/password credentials for authentication")
        else:
            logger.debug("Using session cookies for authentication")
            
        try:
            logger.info(f"Starting to fetch posts from group {group_id}")
            post_generator = fb_scraper.get_posts(
                group=group_id,
                pages=self.max_pages,
                options=options,
                cookies=cookies
            )
            
            posts_counter = 0
            for post in post_generator:
                posts_counter += 1
                logger.debug(f"Fetched post #{posts_counter}")
                
                if len(posts) >= self.max_posts:
                    logger.debug(f"Reached maximum posts limit ({self.max_posts})")
                    break
                    
                # Skip posts without text
                if not post.get('text'):
                    logger.debug("Skipping post with no text")
                    continue
                    
                posts.append(post)
                logger.debug(f"Added post with text length: {len(post.get('text', ''))}")
                time.sleep(self.delay)
                
            logger.info(f"Retrieved {len(posts)} posts from group {group_id} (processed {posts_counter} total)")
            
        except Exception as e:
            logger.error(f"Error scraping group {group_id}: {e}")
            logger.error(traceback.format_exc())
            
        return posts
        
    def _scrape_group_with_selenium(self, group_id, email=None, password=None):
        """Fallback method to scrape a Facebook group using Selenium."""
        try:
            # Import the Selenium libraries directly instead of using facebook_page_scraper
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            logger.info(f"Attempting fallback scraping of group {group_id} with Selenium")
            
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--mute-audio")
            # Keep browser visible for debugging - change to True for production
            chrome_options.headless = False
            
            # Initialize the browser
            browser = webdriver.Chrome(options=chrome_options)
            
            try:
                # Login to Facebook if credentials are provided
                if email and password:
                    logger.info("Logging into Facebook with provided credentials")
                    browser.get("https://www.facebook.com/")
                    
                    # Handle cookies popup if it appears
                    try:
                        cookie_buttons = WebDriverWait(browser, 5).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-cookiebanner='accept_button']"))
                        )
                        for button in cookie_buttons:
                            if "Accept" in button.text or "Accept All" in button.text:
                                button.click()
                                break
                    except Exception as e:
                        logger.debug(f"No cookie banner found or error: {e}")
                    
                    # Enter login credentials
                    try:
                        email_field = WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located((By.ID, "email"))
                        )
                        password_field = browser.find_element(By.ID, "pass")
                        login_button = browser.find_element(By.NAME, "login")
                        
                        email_field.send_keys(email)
                        password_field.send_keys(password)
                        login_button.click()
                        
                        # Wait for login to complete
                        time.sleep(5)
                        logger.info("Logged in with Selenium")
                    except Exception as e:
                        logger.error(f"Login failed: {e}")
                
                # Navigate to the group
                group_url = f"https://www.facebook.com/groups/{group_id}"
                browser.get(group_url)
                logger.info(f"Navigated to group: {group_url}")
                
                # Wait for page to load
                time.sleep(5)
                
                # Scroll to load more posts
                for _ in range(3):  # Scroll 3 times
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Extract posts
                posts = []
                post_elements = browser.find_elements(By.CSS_SELECTOR, "[data-pagelet^='FeedUnit_']")
                if not post_elements:
                    # Try alternative selector
                    post_elements = browser.find_elements(By.CSS_SELECTOR, "div[role='article']")
                    
                logger.info(f"Found {len(post_elements)} post elements")
                
                for i, post_element in enumerate(post_elements[:self.max_posts]):
                    try:
                        # Extract author name
                        author_elements = post_element.find_elements(By.CSS_SELECTOR, "a[href*='/user/']") or \
                                         post_element.find_elements(By.CSS_SELECTOR, "a[aria-label]") or \
                                         post_element.find_elements(By.CSS_SELECTOR, "h3 a")
                        
                        username = "N/A"
                        user_url = None
                        
                        for author_el in author_elements:
                            if author_el.text and author_el.get_attribute("href"):
                                username = author_el.text
                                user_url = author_el.get_attribute("href")
                                break
                        
                        # Extract post text
                        text_elements = post_element.find_elements(By.CSS_SELECTOR, "div[data-ad-comet-preview='message']") or \
                                       post_element.find_elements(By.CSS_SELECTOR, "div[data-ad-preview='message']") or \
                                       post_element.find_elements(By.CSS_SELECTOR, "div.userContent") or \
                                       post_element.find_elements(By.CSS_SELECTOR, "span")
                        
                        post_text = ""
                        for text_el in text_elements:
                            if text_el.text and len(text_el.text) > 10:  # Avoid small pieces of text like buttons
                                post_text += text_el.text + "\n"
                                break  # Just get the main content
                        
                        # Only add post if we have text
                        if post_text.strip():
                            # Create post object
                            post = {
                                'post_id': f"selenium_{i}_{group_id}",
                                'username': username,
                                'user_url': user_url,
                                'text': post_text.strip(),
                                'time': None,
                                'link': None,
                            }
                            
                            posts.append(post)
                            logger.debug(f"Extracted post {i} from {username}")
                    except Exception as e:
                        logger.error(f"Error extracting post {i}: {e}")
                
                logger.info(f"Retrieved {len(posts)} posts from group {group_id} using Selenium")
                return posts
                
            finally:
                # Always close the browser
                browser.quit()
                
        except Exception as e:
            logger.error(f"Selenium fallback failed for group {group_id}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def scrape_group(self, group_id, use_selenium_fallback=False, email=None, password=None, cookies=None):
        """Main method to scrape a Facebook group."""
        posts = self._scrape_group_with_http(group_id, cookies)
        
        # If HTTP-based approach failed or returned no results, try Selenium as fallback
        if not posts and use_selenium_fallback:
            logger.info(f"HTTP-based scraping returned no posts for group {group_id}, trying Selenium fallback")
            # Wait a bit before trying the fallback to avoid rate limiting
            time.sleep(self.delay * 2)
            posts = self._scrape_group_with_selenium(group_id, email, password)
            
        return posts