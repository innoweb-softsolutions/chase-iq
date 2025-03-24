"""
Scrapers for Facebook content using Selenium
"""
import time
import logging
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from .extractors import PostExtractor

logger = logging.getLogger(__name__)

class FacebookScraper:
    """Base class for Facebook scrapers."""
    
    def __init__(self, browser_manager):
        """Initialize the scraper with a browser manager."""
        self.browser_manager = browser_manager
        self.browser = None
    
    def _get_browser(self):
        """Get or initialize the browser."""
        if not self.browser:
            self.browser = self.browser_manager.setup_browser()
        return self.browser
    
    def _scroll_page(self, max_scrolls=10):
        """Scroll the page to load more content."""
        browser = self._get_browser()
        
        last_height = browser.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        
        while scroll_attempts < max_scrolls:
            # Scroll down to bottom
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(3)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If heights are the same, stop scrolling
                logger.info("No more new content loading, stopping scroll")
                break
            last_height = new_height
            scroll_attempts += 1
            
            # Log progress
            logger.debug(f"Scroll {scroll_attempts}/{max_scrolls} completed")


class GroupScraper(FacebookScraper):
    """Scrapes content from Facebook groups."""
    
    def __init__(self, browser_manager):
        """Initialize the group scraper."""
        super().__init__(browser_manager)
        self.post_extractor = PostExtractor()
    
    def scrape_group(self, group_id, max_posts=10):
        """Scrape posts from a Facebook group."""
        logger.info(f"Scraping group: {group_id}")
        browser = self._get_browser()
        
        posts = []
        
        try:
            # Navigate to the group
            group_url = f"https://www.facebook.com/groups/{group_id}"
            browser.get(group_url)
            logger.info(f"Navigated to group: {group_url}")
            
            # Initial wait for page load
            time.sleep(5)
            
            # Take a screenshot for debugging
            self.browser_manager.take_screenshot(f"{group_id}_screenshot.png")
            
            # Log current URL to ensure we're on the right page
            logger.info(f"Current URL after navigation: {browser.current_url}")
            
            # Check for private group
            if self._is_private_group(group_id):
                return []  # Return empty list if private group
            
            # Scroll to load more content
            self._scroll_page()
            
            # Find post elements
            post_elements = self._find_post_elements()
            
            if not post_elements:
                logger.warning("No posts found with any selector")
                # Debug: Save the page source to a file to inspect
                self._save_page_source(group_id)
                return posts
            
            # Process posts
            posts = self._process_posts(post_elements, group_id, max_posts)
            
            # Debug: If no posts found, save the page source
            if not posts:
                self._save_page_source(group_id)
            
            logger.info(f"Successfully extracted {len(posts)} posts from group {group_id}")
            
        except Exception as e:
            logger.error(f"Error scraping group: {e}")
            logger.error(traceback.format_exc())
            
        return posts
    
    def _is_private_group(self, group_id):
        """Check if a group is private and requires membership."""
        browser = self._get_browser()
        
        try:
            join_buttons = WebDriverWait(browser, 3).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@role='main']//span[contains(text(), 'Join Group')]"))
            )
            
            # Check if the button is prominently displayed (not just a small link)
            for button in join_buttons:
                # Check if the button is visible and prominent
                if button.is_displayed():
                    try:
                        # Check if it's within a button container
                        parent = button.find_element(By.XPATH, "./ancestor::div[@role='button' or contains(@class, 'button')]")
                        if parent:
                            logger.warning("This is a private group requiring membership")
                            # Save additional screenshot of the join button area
                            self.browser_manager.take_screenshot(f"{group_id}_join_button.png")
                            return True
                    except:
                        # If we can't find a proper button parent, it might just be a link
                        pass
        except (TimeoutException, NoSuchElementException):
            # No join button found, likely a public group or already joined
            logger.debug("No prominent join button found, proceeding with scraping")
        
        return False
    
    def _find_post_elements(self):
        """Find post elements on the page using various selectors."""
        browser = self._get_browser()
        
        # Updated Facebook post selectors (2024)
        selectors = [
            "div[role='article']",                       # Most common post container
            "div.x1yztbdb",                              # Facebook class for feed items
            "div.x1lliihq",                              # Another Facebook feed container
            "div.x193iq5w",                              # Recent Facebook post class
            "div.x1r8uery",                              # Another Facebook content container
            "div[data-pagelet^='FeedUnit_']",            # Feed units
            "div.x1lq5wgf.xgqcy7u.x30kzoy.x9jhf4c.x1ldc2hk", # Recent timeline posts
            "div.x78zum5.x1n2onr6"                       # Common 2024 feed container
        ]
        
        post_elements = []
        
        for selector in selectors:
            try:
                # Use WebDriverWait to ensure elements are loaded
                elements = WebDriverWait(browser, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if elements:
                    post_elements = elements
                    logger.info(f"Found {len(post_elements)} posts using selector: {selector}")
                    break
            except (TimeoutException, NoSuchElementException):
                logger.debug(f"No posts found with selector: {selector}")
        
        return post_elements
    
    def _process_posts(self, post_elements, group_id, max_posts):
        """Process post elements and extract data."""
        posts = []
        
        # Limit to max_posts
        post_elements = post_elements[:max_posts] if max_posts else post_elements
        
        for i, post_element in enumerate(post_elements):
            try:
                # Use the PostExtractor to extract data from each post
                post_data = self.post_extractor.extract_post_data(
                    post_element, 
                    self._get_browser(), 
                    f"{group_id}_{i}"
                )
                
                if post_data:
                    posts.append(post_data)
                    logger.debug(f"Extracted post #{i} from {post_data.get('username', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error processing post {i}: {e}")
        
        return posts
    
    def _save_page_source(self, group_id):
        """Save the page source for debugging."""
        browser = self._get_browser()
        
        try:
            debug_path = f"{group_id}_page_source.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(browser.page_source)
            logger.info(f"Saved page source to {debug_path} for debugging")
        except Exception as e:
            logger.error(f"Error saving page source: {e}")


class PageScraper(FacebookScraper):
    """Scrapes content from Facebook pages."""
    
    def __init__(self, browser_manager):
        """Initialize the page scraper."""
        super().__init__(browser_manager)
        self.group_scraper = GroupScraper(browser_manager)
    
    def scrape_page(self, page_name, max_posts=10):
        """Scrape posts from a Facebook page."""
        logger.info(f"Scraping page: {page_name}")
        browser = self._get_browser()
        
        try:
            # Construct the URL
            page_url = f"https://www.facebook.com/{page_name}"
            browser.get(page_url)
            logger.info(f"Navigated to page: {page_url}")
            
            # Pause to let page load
            time.sleep(5)
            
            # Take a screenshot for debugging
            self.browser_manager.take_screenshot(f"{page_name}_screenshot.png")
            
            # Use GroupScraper to handle the actual content extraction
            # (Pages use similar DOM structure to groups)
            logger.info(f"Scraping page content for: {page_name}")
            posts = self.group_scraper.scrape_group(page_name, max_posts)
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            logger.error(traceback.format_exc())
            return []