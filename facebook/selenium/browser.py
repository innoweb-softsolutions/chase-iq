"""
Browser setup and management for Facebook scraping
"""
import os
import time
import logging
import pickle

# Use undetected-chromedriver for better anti-detection
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

class BrowserManager:
    """Handles browser creation, configuration, and cleanup."""
    
    def __init__(self, headless=False, timeout=45, cookies_file='facebook_cookies.pkl'):
        """Initialize the browser manager."""
        self.headless = headless
        self.timeout = timeout
        self.browser = None
        self.cookies_file = cookies_file
        
    def setup_browser(self):
        """Initialize and configure the browser with anti-detection measures."""
        if self.browser:
            return self.browser
            
        try:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            
            # Add common options to make browser more reliable
            options.add_argument("--disable-notifications")
            options.add_argument("--mute-audio")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Additional stability options
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--dns-prefetch-disable")
            
            # Add user agent to appear more like a real browser
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
            
            # Create browser instance with undetected-chromedriver
            self.browser = uc.Chrome(options=options)
            
            # Set increased timeouts for stability
            self.browser.set_page_load_timeout(self.timeout)
            self.browser.implicitly_wait(10)
            
            logger.info("Browser initialized successfully with undetected-chromedriver")
            return self.browser
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def save_cookies(self):
        """Save browser cookies to a file."""
        if not self.browser:
            logger.warning("Cannot save cookies: Browser not initialized")
            return False
            
        try:
            cookies = self.browser.get_cookies()
            with open(self.cookies_file, 'wb') as file:
                pickle.dump(cookies, file)
            logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False
    
    def load_cookies(self):
        """Load cookies from file into the browser."""
        if not self.browser:
            logger.warning("Cannot load cookies: Browser not initialized")
            return False
            
        if not os.path.exists(self.cookies_file):
            logger.info("No cookies file found")
            return False
            
        try:
            with open(self.cookies_file, 'rb') as file:
                cookies = pickle.load(file)
                
            # Need to be on a facebook domain to add cookies
            self.browser.get("https://www.facebook.com/")
            time.sleep(2)
            
            for cookie in cookies:
                try:
                    self.browser.add_cookie(cookie)
                except Exception as cookie_error:
                    logger.warning(f"Error adding cookie: {cookie_error}")
                    
            logger.info(f"Loaded {len(cookies)} cookies from file")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False
    
    def take_screenshot(self, filename):
        """Take a screenshot and save it to the specified file."""
        if not self.browser:
            logger.warning("Cannot take screenshot: Browser not initialized")
            return None
            
        try:
            self.browser.save_screenshot(filename)
            logger.info(f"Screenshot saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    def close(self):
        """Close the browser and clean up resources."""
        if self.browser:
            try:
                self.browser.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.browser = None