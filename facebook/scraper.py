"""
Facebook Lead Scraper - Main implementation
"""
import os
import logging
import time
import json
import pandas as pd
from datetime import datetime
import facebook_scraper as fb_scraper

from .extractors.group_extractor import GroupExtractor
from .extractors.profile_extractor import ProfileExtractor
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
        
        # Initialize extractors
        self.group_extractor = GroupExtractor(max_posts, max_pages, DELAY_BETWEEN_REQUESTS)
        self.profile_extractor = ProfileExtractor(DELAY_BETWEEN_REQUESTS)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up cookies file if credentials are provided
        self.cookies = None
        if self.email and self.password:
            try:
                # Updated authentication method
                self.cookies = fb_scraper.get_cookies(self.email, self.password)
                logger.info("Successfully set up cookies from login")
            except AttributeError:
                # Fallback to old method if available
                try:
                    fb_scraper.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
                    fb_scraper.enable_logging()
                    # Just set credentials for later use
                    self.cookies = {"email": self.email, "pass": self.password}
                    logger.info("Set up credentials for later authentication")
                except Exception as e:
                    logger.warning(f"Failed to set up any authentication: {e}")
            except Exception as e:
                logger.warning(f"Failed to set up cookies: {e}")
        
    def scrape_groups(self):
        """Scrape all configured Facebook groups."""
        all_posts = []
        
        for group in self.groups:
            try:
                logger.info(f"Starting to scrape group: {group}")
                posts = self.group_extractor.scrape_group(
                    group,
                    use_selenium_fallback=self.use_browser_fallback,
                    email=self.email, 
                    password=self.password,
                    cookies=self.cookies
                )
                all_posts.extend(posts)
                logger.info(f"Finished scraping group {group}: {len(posts)} posts")
                
                # Avoid rate limiting - increased delay
                time.sleep(DELAY_BETWEEN_REQUESTS * 2)
                
            except Exception as e:
                logger.error(f"Error scraping group {group}: {e}")
                
        return all_posts
    
    def scrape_pages(self):
        """Scrape all configured Facebook pages."""
        all_posts = []
        
        for page in self.pages:
            try:
                logger.info(f"Starting to scrape page: {page}")
                
                # If we have credentials, try to use them
                options = {"posts_per_page": 10}
                if isinstance(self.cookies, dict) and "email" in self.cookies:
                    options["credentials"] = (self.cookies["email"], self.cookies["pass"])
                
                posts = list(fb_scraper.get_posts(
                    account=page,
                    pages=self.max_pages,
                    options=options,
                    cookies=self.cookies if not isinstance(self.cookies, dict) else None
                ))
                
                all_posts.extend(posts[:self.max_posts])
                logger.info(f"Finished scraping page {page}: {len(posts[:self.max_posts])} posts")
                
                # Avoid rate limiting - increased delay
                time.sleep(DELAY_BETWEEN_REQUESTS * 2)
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                
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