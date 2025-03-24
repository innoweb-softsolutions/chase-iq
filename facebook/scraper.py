"""
Facebook Lead Scraper - Main implementation (simplified)
"""
import os
import logging
import time
import pandas as pd
from datetime import datetime

# Import our custom selenium scraper
from .selenium_scraper import FacebookSeleniumScraper
from .utils.data_processor import DataProcessor
from .config import (
    FB_EMAIL, FB_PASSWORD, FB_GROUPS, FB_PAGES, 
    MAX_POSTS, MAX_PAGES, USE_BROWSER, OUTPUT_DIR,
    DELAY_BETWEEN_REQUESTS
)

logger = logging.getLogger(__name__)

class FacebookScraper:
    """Main class for scraping lead information from Facebook."""
    
    def __init__(self, 
                groups=None, 
                pages=None, 
                max_posts=MAX_POSTS, 
                max_pages=MAX_PAGES,
                use_browser_fallback=USE_BROWSER,
                email=FB_EMAIL,
                password=FB_PASSWORD,
                output_dir=OUTPUT_DIR):
        """Initialize the Facebook Lead Scraper."""
        self.groups = groups or FB_GROUPS
        self.pages = pages or FB_PAGES
        self.max_posts = max_posts
        self.max_pages = max_pages
        self.use_browser_fallback = use_browser_fallback
        self.email = email
        self.password = password
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("Initializing Facebook scraper with Selenium")
        
    def scrape_groups(self):
        """Scrape all configured Facebook groups."""
        all_posts = []
        
        # Create a single scraper instance
        scraper = FacebookSeleniumScraper(
            email=self.email, 
            password=self.password,
            headless=False  # Set to False to see what's happening
        )

        
        try:
            login_success = scraper.login()
            if login_success:
                logger.info("Successfully logged in to Facebook")
            else:
                logger.warning("Failed to log in to Facebook - content may be restricted")
            # Scrape each group
            for group in self.groups:
                try:
                    logger.info(f"Starting to scrape group: {group}")
                    posts = scraper.scrape_group(
                        group,
                        max_posts=self.max_posts
                    )
                    
                    all_posts.extend(posts)
                    logger.info(f"Finished scraping group {group}: {len(posts)} posts")
                    
                    # Add delay between groups
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                    
                except Exception as e:
                    logger.error(f"Error scraping group {group}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        finally:
            # Always close the browser
            scraper.close()
                
        return all_posts
    
    def scrape_pages(self):
        """Scrape all configured Facebook pages."""
        all_posts = []
        
        # Create a single scraper instance
        scraper = FacebookSeleniumScraper(
            email=self.email, 
            password=self.password,
            headless=False
        )
        
        try:
            login_success = scraper.login()
            if login_success:
                logger.info("Successfully logged in to Facebook")
            else:
                logger.warning("Failed to log in to Facebook - content may be restricted")
            # Scrape each page
            for page in self.pages:
                try:
                    logger.info(f"Starting to scrape page: {page}")
                    posts = scraper.scrape_page(
                        page,
                        max_posts=self.max_posts
                    )
                    
                    all_posts.extend(posts)
                    logger.info(f"Finished scraping page {page}: {len(posts)} posts")
                    
                    # Add delay between pages
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                    
                except Exception as e:
                    logger.error(f"Error scraping page {page}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        finally:
            # Always close the browser
            scraper.close()
                
        return all_posts
    
    def process_posts(self, posts):
        """Process posts to extract leads."""
        # Use data processor to format posts for email finder pipeline
        return DataProcessor.format_for_pipeline(posts)
    
    def save_to_csv(self, leads):
        """Save leads to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"facebook_leads_{timestamp}.csv")
        
        # Create a DataFrame (even if empty)
        df = pd.DataFrame(leads)
        
        # If DataFrame is empty, add columns to match expected format
        if df.empty:
            df = pd.DataFrame(columns=[
                "Name", "Title", "Company", "Profile URL", "Email", "Website"
            ])
        
        df.to_csv(filename, index=False)
        
        logger.info(f"Saved {len(leads)} leads to {filename}")
        return filename
    
    def run(self):
        """Run the Facebook lead scraper."""
        all_posts = []
        
        # Scrape groups
        if self.groups:
            group_posts = self.scrape_groups()
            all_posts.extend(group_posts)
            logger.info(f"Scraped {len(group_posts)} posts from {len(self.groups)} groups")
            
        # Scrape pages
        if self.pages:
            page_posts = self.scrape_pages()
            all_posts.extend(page_posts)
            logger.info(f"Scraped {len(page_posts)} posts from {len(self.pages)} pages")
            
        # Extract leads from posts
        leads = self.process_posts(all_posts)
        logger.info(f"Extracted {len(leads)} leads from {len(all_posts)} posts")
        
        # Save leads to CSV
        output_file = self.save_to_csv(leads)
        
        return output_file