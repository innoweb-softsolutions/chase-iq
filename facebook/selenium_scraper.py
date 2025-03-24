"""
Standalone Selenium-based Facebook scraper with improved scrolling and cookie handling
"""
import logging
import time
import os
import json
import pickle
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class FacebookSeleniumScraper:
    """Scrape Facebook content using Selenium with improved post loading."""
    
    def __init__(self, email=None, password=None, headless=False, timeout=30, delay=5):
        """Initialize the scraper."""
        self.email = email
        self.password = password
        self.headless = headless
        self.timeout = timeout
        self.delay = delay
        self.browser = None
        self.logged_in = False
        self.cookies_file = 'facebook_cookies.pkl'
        
    def __enter__(self):
        """Set up browser when using with context manager."""
        self.setup_browser()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser when exiting context manager."""
        self.close()
        
    def setup_browser(self):
        """Set up the Chrome browser."""
        if self.browser:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Add common options to make browser more reliable
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add user agent to appear more like a real browser
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        
        # Create and store the browser instance
        self.browser = webdriver.Chrome(options=chrome_options)
        self.browser.implicitly_wait(10)
        logger.info("Browser initialized successfully")
        
    def close(self):
        """Close the browser and clean up resources."""
        if self.browser:
            try:
                # Save cookies before closing if we're logged in
                if self.logged_in:
                    self.save_cookies()
                    
                self.browser.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            self.browser = None
            logger.info("Browser closed")
            
    def save_cookies(self):
        """Save cookies to file for future sessions."""
        try:
            cookies = self.browser.get_cookies()
            with open(self.cookies_file, 'wb') as file:
                pickle.dump(cookies, file)
            logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            
    def load_cookies(self):
        """Load cookies from file if available."""
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
            
    def login(self):
        """Log in to Facebook with cookie support."""
        self.setup_browser()
        
        # First try to use saved cookies
        if self.load_cookies():
            # Navigate to Facebook to verify login status
            self.browser.get("https://www.facebook.com/")
            time.sleep(5)
            
            # Check if we're logged in
            if "login" not in self.browser.current_url.lower():
                logger.info("Successfully logged in with cookies")
                self.logged_in = True
                return True
            else:
                logger.warning("Cookie login failed, will try regular login")
        
        # If no cookies or cookie login failed, try regular login
        if not self.email or not self.password:
            logger.warning("No login credentials provided")
            return False
            
        logger.info("Attempting to log in to Facebook with credentials")
        
        try:
            # Navigate to Facebook login page
            self.browser.get("https://www.facebook.com/")
            
            # Handle cookie consent if present
            try:
                cookie_buttons = WebDriverWait(self.browser, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-cookiebanner='accept_button']"))
                )
                for button in cookie_buttons:
                    if "Accept" in button.text or "Accept All" in button.text:
                        button.click()
                        logger.debug("Accepted cookies")
                        break
            except (TimeoutException, NoSuchElementException):
                logger.debug("No cookie banner found or it was already handled")
            
            # Wait for login form
            try:
                email_field = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                password_field = self.browser.find_element(By.ID, "pass")
                
                # Input credentials
                email_field.send_keys(self.email)
                password_field.send_keys(self.password)
                
                # Find and click login button
                login_button = self.browser.find_element(By.NAME, "login")
                login_button.click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Save screenshot for debugging
                screenshot_path = "facebook_login_attempt.png"
                self.browser.save_screenshot(screenshot_path)
                logger.info(f"Login attempt screenshot saved to {screenshot_path}")
                
                # Check for login issues or security checkpoints
                if ("checkpoint" in self.browser.current_url.lower() or 
                    "login" in self.browser.current_url.lower()):
                    
                    logger.warning("Facebook security checkpoint detected or login failed")
                    logger.info("Waiting for manual login - Please complete the login in the browser window")
                    
                    # Extended wait for manual intervention
                    manual_wait = 180  # 3 minutes for manual login
                    logger.info(f"Waiting {manual_wait} seconds for manual login")
                    time.sleep(manual_wait)
                    
                    # Check login status again
                    if "login" not in self.browser.current_url.lower():
                        logger.info("Manual login appears successful")
                        self.logged_in = True
                        self.save_cookies()  # Save cookies after successful manual login
                        return True
                    else:
                        logger.error("Manual login also failed")
                        return False
                
                # Try to detect successful login
                try:
                    # Check for common elements that appear after login
                    WebDriverWait(self.browser, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='navigation']")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Home']")),
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div[aria-label='Facebook']"))
                        )
                    )
                    logger.info("Login successful - found post-login elements")
                    self.logged_in = True
                    self.save_cookies()  # Save cookies after successful login
                    return True
                except:
                    logger.error("Couldn't find post-login elements")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to log in: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
        
    def scrape_group(self, group_id, max_posts=10):
        """Scrape posts from a Facebook group with improved scrolling."""
        logger.info(f"Scraping group: {group_id}")
        self.setup_browser()
        
        posts = []
        
        try:
            # Navigate to the group
            group_url = f"https://www.facebook.com/groups/{group_id}"
            self.browser.get(group_url)
            logger.info(f"Navigated to group: {group_url}")
            
            # Initial wait for page load
            time.sleep(5)
            
            # Take a screenshot for debugging
            screenshot_path = f"{group_id}_screenshot.png"
            self.browser.save_screenshot(screenshot_path)
            logger.info(f"Group page screenshot saved to {screenshot_path}")
            
            # Check if Join Group button is present
            try:
                join_buttons = self.browser.find_elements(By.XPATH, "//span[contains(text(), 'Join Group')]")
                if join_buttons:
                    logger.warning("This is a private group requiring membership")
            except:
                pass
                
            # Improved progressive scrolling logic to load more content
            last_height = self.browser.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 10
            
            while scroll_attempts < max_scrolls:
                # Scroll down to bottom
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load page
                time.sleep(3)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.browser.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # If heights are the same after 3 attempts, stop scrolling
                    logger.info("No more new content loading, stopping scroll")
                    break
                last_height = new_height
                scroll_attempts += 1
                
                # Log progress
                logger.debug(f"Scroll {scroll_attempts}/{max_scrolls} completed")
            
            # Updated Facebook post selectors (2024)
            post_elements = []
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
            
            for selector in selectors:
                post_elements = self.browser.find_elements(By.CSS_SELECTOR, selector)
                if post_elements:
                    logger.info(f"Found {len(post_elements)} posts using selector: {selector}")
                    break
            
            # Process each post (limited to max_posts)
            for i, post_element in enumerate(post_elements[:max_posts]):
                try:
                    # Try to extract username
                    username = "Unknown"
                    profile_url = None
                    
                    # Updated author selectors for 2024 Facebook
                    author_selectors = [
                        "h3 a", 
                        "a[role='link']:not([aria-hidden='true'])",
                        "span.x1i10hfl a",                         # Recent profile links
                        "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq a", # Profile link class
                        "a.x1i10hfl"                              # Common Facebook link class
                    ]
                    
                    for author_selector in author_selectors:
                        author_elements = post_element.find_elements(By.CSS_SELECTOR, author_selector)
                        for author_el in author_elements:
                            try:
                                if author_el.text and len(author_el.text) > 0:
                                    # Skip common non-author elements
                                    text = author_el.text.lower()
                                    if text in ["like", "comment", "share", "save", "follow"]:
                                        continue
                                        
                                    username = author_el.text
                                    try:
                                        profile_url = author_el.get_attribute("href")
                                        # Skip if it's a reaction link
                                        if "reaction/profile" in profile_url or "comment" in profile_url:
                                            continue
                                    except:
                                        pass
                                    break
                            except:
                                continue
                        if username != "Unknown":
                            break
                    
                    # Extract post text with updated selectors
                    post_text = ""
                    text_selectors = [
                        "div[data-ad-comet-preview='message']", 
                        "div[data-ad-preview='message']", 
                        "div.x1iorvi4",                           # Content class 
                        "div.xdj266r",                            # Another content class
                        "div.x11i5rnm",                           # Common text container
                        "div.x1cy8zhl",                           # Post text container
                        "div[dir='auto']",                        # Text direction containers
                        "span[dir='auto']"                        # Text direction spans
                    ]
                    
                    for text_selector in text_selectors:
                        text_elements = post_element.find_elements(By.CSS_SELECTOR, text_selector)
                        for text_el in text_elements:
                            try:
                                if text_el.text and len(text_el.text) > 10:  # Minimum text length
                                    # Skip if it's a common UI text
                                    if text_el.text.lower() in ["see more", "see less", "view more comments"]:
                                        continue
                                    post_text += text_el.text + "\n"
                            except:
                                continue
                        if post_text:
                            break
                    
                    # Extract links (potential websites)
                    links = []
                    try:
                        link_elements = post_element.find_elements(By.CSS_SELECTOR, "a[href]:not([role='button']):not([href*='facebook.com']):not([href*='fb.com'])")
                        for link_el in link_elements:
                            try:
                                href = link_el.get_attribute("href")
                                if href and "facebook.com" not in href and "fb.com" not in href:
                                    links.append(href)
                            except:
                                continue
                    except:
                        pass
                    
                    # Only create post if we have meaningful content
                    if post_text or links:
                        post = {
                            'post_id': f"{group_id}_{i}",
                            'username': username,
                            'user_url': profile_url,
                            'text': post_text.strip(),
                            'link': links[0] if links else None,
                            'links': links
                        }
                        
                        posts.append(post)
                        logger.debug(f"Extracted post from {username}")
                    
                except Exception as e:
                    logger.error(f"Error extracting post {i}: {e}")
                    continue
            
            # Debug: If no posts found, save the page source
            if not posts:
                # Debug: Save the page source to a file to inspect
                debug_path = f"{group_id}_page_source.html"
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(self.browser.page_source)
                logger.info(f"Saved page source to {debug_path} for debugging")
            
            logger.info(f"Successfully extracted {len(posts)} posts from group {group_id}")
            
        except Exception as e:
            logger.error(f"Error scraping group: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        return posts
        
    def scrape_page(self, page_name, max_posts=10):
        """Scrape posts from a Facebook page."""
        logger.info(f"Scraping page: {page_name}")
        self.setup_browser()
        
        try:
            # Construct the URL
            page_url = f"https://www.facebook.com/{page_name}"
            self.browser.get(page_url)
            logger.info(f"Navigated to page: {page_url}")
            
            # Pause to let page load
            time.sleep(5)
            
            # Take a screenshot for debugging
            screenshot_path = f"{page_name}_screenshot.png"
            self.browser.save_screenshot(screenshot_path)
            logger.info(f"Page screenshot saved to {screenshot_path}")
            
            # Direct scrape using the same logic as groups
            posts = self.scrape_group(page_name, max_posts)
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []