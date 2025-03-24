"""
Standalone Selenium-based Facebook scraper
Main integration point for all Selenium components
"""
import logging
import time
from .selenium.browser import BrowserManager
from .selenium.auth import FacebookAuthenticator
from .selenium.scrapers import GroupScraper, PageScraper

logger = logging.getLogger(__name__)

class FacebookSeleniumScraper:
    """Facebook scraper using Selenium with improved stability and reliability."""
    
    def __init__(self, email=None, password=None, headless=False, timeout=45, delay=5):
        """Initialize the scraper with configuration options."""
        self.email = email
        self.password = password
        self.headless = headless
        self.timeout = timeout
        self.delay = delay
        self.logged_in = False
        self.cookies_file = 'facebook_cookies.pkl'
        
        # Initialize components
        self.browser_manager = BrowserManager(
            headless=headless,
            timeout=timeout,
            cookies_file=self.cookies_file
        )
        self.authenticator = FacebookAuthenticator(
            self.browser_manager,
            email=email,
            password=password
        )
        self.group_scraper = GroupScraper(self.browser_manager)
        self.page_scraper = PageScraper(self.browser_manager)
    
    def __enter__(self):
        """Set up scraper when using with context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up when exiting context manager."""
        self.close()
    
    def login(self):
        """Log in to Facebook."""
        login_success = self.authenticator.login()
        if login_success:
            self.logged_in = True
        return login_success
    
    def scrape_group(self, group_id, max_posts=10):
        """Scrape posts from a Facebook group."""
        if not self.logged_in:
            logger.warning("Not logged in. Attempting login...")
            if not self.login():
                logger.error("Login failed, proceeding with limited access")
        
        return self.group_scraper.scrape_group(group_id, max_posts)
    
    def scrape_page(self, page_name, max_posts=10):
        """Scrape posts from a Facebook page."""
        if not self.logged_in:
            logger.warning("Not logged in. Attempting login...")
            if not self.login():
                logger.error("Login failed, proceeding with limited access")
        
        return self.page_scraper.scrape_page(page_name, max_posts)
    
    def close(self):
        """Close the browser and clean up resources."""
        self.browser_manager.close()