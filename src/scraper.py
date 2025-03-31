"""
LinkedIn Sales Navigator Scraper - Core Scraping Logic
"""
import os
import pickle
import time
import random
import undetected_chromedriver as uc
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import logging
import json
import re

from config.config import *
from src.utils.helpers import take_debug_screenshot, extract_email, extract_website, extract_linkedin_profile_url, remove_emoji

class LinkedInScraper:
    """LinkedIn Sales Navigator Scraper Class"""
    
    def __init__(self):
        """Initialize the scraper with browser settings."""
        self.setup_browser()
        self.scrape_history_file = "output/scrape_history.json"
        self.scrape_history = self._load_scrape_history()
        self.current_url = None
        
    def setup_browser(self):
        """Set up the undetected Chrome browser."""
        options = uc.ChromeOptions()
        options.headless = HEADLESS_MODE
        
        # Apply user agent rotation if enabled
        if USER_AGENT_ROTATION:
            options.add_argument(f"user-agent={UserAgent().random}")
        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        
        # Add random viewport size if enabled
        if 'RANDOM_VIEWPORT_SIZE' in globals() and RANDOM_VIEWPORT_SIZE:
            width = random.randint(1024, 1920)
            height = random.randint(768, 1080)
            options.add_argument(f"--window-size={width},{height}")
        
        self.driver = uc.Chrome(options=options)
        
        # Set page load timeout from config
        if 'REQUEST_TIMEOUT' in globals():
            self.driver.set_page_load_timeout(REQUEST_TIMEOUT)
    
    def _load_scrape_history(self):
        """Load scraping history from file."""
        if os.path.exists(self.scrape_history_file):
            try:
                with open(self.scrape_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARNING] Error loading scrape history: {e}")
                return {}
        return {}
    
    def _save_scrape_history(self):
        """Save scraping history to file."""
        os.makedirs(os.path.dirname(self.scrape_history_file), exist_ok=True)
        try:
            with open(self.scrape_history_file, 'w') as f:
                json.dump(self.scrape_history, f)
            print(f"[INFO] Scrape history saved.")
        except Exception as e:
            print(f"[WARNING] Error saving scrape history: {e}")
    
    def check_previous_scrape(self, url):
        """Check if URL was previously scraped and automatically continue."""
        self.current_url = url
    
        if url in self.scrape_history:
            last_page = self.scrape_history[url].get('last_page', 1)
            last_scraped = self.scrape_history[url].get('last_scraped', 'unknown date')
        
            print(f"[INFO] This URL was previously scraped (reached page {last_page}) on {last_scraped}. Continuing automatically.")
        
            # Update the timestamp and continue from where we left off
            self.scrape_history[url]['last_scraped'] = time.strftime('%Y-%m-%d %H:%M:%S')
            return last_page  # Continue from last page
        else:
            # First time scraping this URL
            self.scrape_history[url] = {
                'last_page': 1,
                'last_scraped': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            return 1  # Start from page 1
        
    def login(self):
        """Handle LinkedIn login through cookies or credentials."""
        print("[INFO] Starting LinkedIn login process...")
        self.driver.get("https://www.linkedin.com/")
        time.sleep(5)
        
        login_successful = False
        
        # Try to use existing cookies first
        if os.path.exists(COOKIE_FILE):
            try:
                print("[INFO] Attempting login with saved cookies...")
                self._load_cookies()
                self.driver.refresh()
                time.sleep(10)
                
                # Check if we're logged in
                if "feed" in self.driver.current_url or "/sales" in self.driver.current_url:
                    login_successful = True
                    print("[OK] Cookie login successful")
                else:
                    print("[WARNING] Saved cookies didn't work, trying credentials...")
            except Exception as e:
                print(f"[WARNING] Error with saved cookies: {e}")
        
        # Fall back to credentials if needed
        if not login_successful:
            try:
                print("[INFO] Attempting login with username and password...")
                self.driver.get("https://www.linkedin.com/login")
                time.sleep(3)
                self._perform_login()
                login_successful = True
            except Exception as e:
                print(f"[ERROR] All login methods failed: {e}")
                take_debug_screenshot(self.driver, "login_failed")
                raise Exception("Could not log in to LinkedIn")
        
        # Navigate to Sales Navigator
        print("[OK] Logged in successfully. Redirecting to Sales Navigator...")
        self.driver.get(SALES_NAV_URL)
        time.sleep(10)
        
        # Check if we were redirected back to login
        if "login" in self.driver.current_url.lower():
            print("[WARNING] LinkedIn redirected to login. Taking debug screenshot...")
            take_debug_screenshot(self.driver, "sales_nav_redirect")
            
            print("[WARNING] Trying to access Sales Navigator again...")
            self.driver.get(SALES_NAV_URL)
            time.sleep(10)
            
        # Final verification
        if "/sales/" not in self.driver.current_url.lower():
            print("[ERROR] Failed to access Sales Navigator. Taking debug screenshot...")
            take_debug_screenshot(self.driver, "sales_nav_failed")
            raise Exception("Could not access Sales Navigator")
            
        print("[OK] Successfully reached Sales Navigator.")
    
    def _load_cookies(self):
        """Load cookies from file."""
        with open(COOKIE_FILE, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        print("[OK] Session cookies loaded.")
    
    def _save_cookies(self):
        """Save cookies to file."""
        os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)
        print("[OK] Session cookies saved.")
    
    def _perform_login(self):
        """Perform manual login with provided credentials."""
        wait = WebDriverWait(self.driver, 20)
        
        try:
            # Wait for the login form to appear
            wait.until(EC.presence_of_element_located((By.ID, "username")))
            
            # Enter credentials and submit
            username_field = self.driver.find_element(By.ID, "username")
            password_field = self.driver.find_element(By.ID, "password")
            
            # Clear fields first to ensure clean input
            username_field.clear()
            username_field.send_keys(LINKEDIN_EMAIL)
            
            password_field.clear()
            password_field.send_keys(LINKEDIN_PASSWORD)
            
            # Click the sign-in button instead of using RETURN key (more reliable)
            sign_in_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            sign_in_button.click()
            
            # Wait for login to complete (longer timeout for security checks)
            time.sleep(10)
            
            # Check if login was successful
            if "checkpoint" in self.driver.current_url or "challenge" in self.driver.current_url:
                print("[WARNING] LinkedIn security checkpoint detected. Manual intervention required.")
                print("[ACTION] Please complete the security verification in the browser.")
                input("[ACTION] Press Enter after completing verification...")
            
            # Save cookies after successful login
            self._save_cookies()
            print("[OK] Login successful")
            
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")
            take_debug_screenshot(self.driver, "login_error")
    
    def human_like_scroll(self):
        """Scroll in a more human-like pattern to avoid detection."""
        # Check scroll behavior setting
        if 'SCROLL_BEHAVIOR' in globals() and SCROLL_BEHAVIOR == "none":
            return
            
        try:
            # Get current scroll height
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Number of scroll steps (random)
            steps = random.randint(3, 7) if SCROLL_BEHAVIOR == "smart" else 3
            
            for i in range(steps):
                # Random scroll distance (percentage of page)
                scroll_percent = random.uniform(0.1, 0.3)
                scroll_y = int(scroll_height * scroll_percent)
                
                # Scroll down with random pause
                self.driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                
                # Add random delays if enabled
                if 'ADD_RANDOM_DELAYS' in globals() and ADD_RANDOM_DELAYS:
                    time.sleep(random.uniform(0.5, 2.0))
                else:
                    time.sleep(0.8)
                
        except Exception as e:
            print(f"[WARNING] Error during scrolling: {e}")
            # Continue execution even if scrolling fails
            pass
    
    def save_profile_links(self, profile_links, filename="output/scraped_profiles.txt"):
        """Save profile links to a file to track already scraped profiles."""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "a") as f:
            for link in profile_links:
                f.write(f"{link}\n")
        print(f"[INFO] Saved {len(profile_links)} profile links to {filename}")

    def load_scraped_profiles(self, filename="output/scraped_profiles.txt"):
        """Load previously scraped profile links to avoid duplicates."""
        # Skip if not enabled in config
        if 'SKIP_ALREADY_SCRAPED' in globals() and not SKIP_ALREADY_SCRAPED:
            return set()
            
        if not os.path.exists(filename):
            return set()
            
        with open(filename, "r") as f:
            return set(line.strip() for line in f if line.strip())
    
    def get_profile_links(self, start_page=1):
        """Extract LinkedIn lead profile URLs from Sales Navigator search results."""
        profile_links = []
        page = start_page
        
        # Load previously scraped profiles to avoid duplicates
        previously_scraped = self.load_scraped_profiles()
        print(f"[INFO] Found {len(previously_scraped)} previously scraped profiles to avoid duplicates")
        
        if page > 1:
            print(f"[INFO] Starting from page {page} based on previous scraping session")
            # Navigate to the starting page
            for p in range(1, page):
                try:
                    print(f"[INFO] Navigating to page {p}...")
                    next_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'artdeco-pagination__button--next')]")
                    if next_buttons and next_buttons[0].is_enabled():
                        next_buttons[0].click()
                        time.sleep(5 + random.uniform(1, 3))
                    else:
                        print("[WARNING] Couldn't navigate to the requested start page. Starting from current page.")
                        break
                except Exception as e:
                    print(f"[WARNING] Error navigating to start page: {e}")
                    break

        while page <= MAX_PAGES and len(profile_links) < MAX_PROFILES:
            print(f"[INFO] Extracting Profile Links from Page {page}...")

            # Scroll until no new content loads
            try:
                print("[INFO] Starting infinite scroll to bottom...")
                time.sleep(2)
                last_height = self.driver.execute_script("return document.querySelector('#search-results-container').scrollHeight")
                while True:
                    # Scroll to bottom of container
                    self.driver.execute_script("document.querySelector('#search-results-container').scrollTo(0, document.querySelector('#search-results-container').scrollHeight)")
                    time.sleep(3)
                    
                    # Calculate new scroll height
                    new_height = self.driver.execute_script("return document.querySelector('#search-results-container').scrollHeight")
                    
                    if new_height == last_height:
                        print("[INFO] Reached bottom of content")
                        time.sleep(3)
                        break
                    last_height = new_height
                
                # Scroll back to top in many small increments
                print("[INFO] Scrolling back to top gradually...")
                total_height = self.driver.execute_script("return document.querySelector('#search-results-container').scrollHeight")
                steps = 15  # Increased number of steps
                for i in range(steps):
                    # Calculate scroll position with slight randomization
                    scroll_position = total_height * (steps - i - 1) / steps
                    scroll_position += random.randint(-50, 50)  # Add small random offset
                    scroll_position = max(0, min(total_height, scroll_position))  # Ensure within bounds
                    
                    self.driver.execute_script(f"document.querySelector('#search-results-container').scrollTo(0, {scroll_position})")
                    time.sleep(random.uniform(0.8, 1.5))  # Random delay between steps
                
                print("[INFO] Waiting for page to stabilize before extracting profiles...")
                time.sleep(8)
                
            except Exception as e:
                print(f"[WARNING] Error during infinite scroll: {e}")
                # Fallback to basic scrolling if container not found
                print("[INFO] Using fallback scroll method...")
                for _ in range(7):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                
                # Fallback gradual scroll back up
                print("[INFO] Scrolling back up gradually (fallback mode)...")
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                steps = 15
                for i in range(steps):
                    scroll_position = total_height * (steps - i - 1) / steps
                    scroll_position += random.randint(-50, 50)
                    scroll_position = max(0, min(total_height, scroll_position))
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                    time.sleep(random.uniform(0.8, 1.5))
                
                time.sleep(8)
            
            # Wait for profile elements to be present
            try:
                print("[INFO] Waiting for profile elements to load...")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/sales/lead/')]"))
                )
            except Exception as e:
                print(f"[WARNING] Timeout waiting for profile elements: {e}")

            print("[INFO] Beginning profile extraction...")
            time.sleep(2)

            # Debug: Take screenshot to verify pagination area
            take_debug_screenshot(self.driver, f"page_{page}_before_extraction")

            # Debug: print a snippet of the page source.
            sample_source = self.driver.page_source[:1000]
            if "sales/lead/" not in sample_source:
                print("[WARNING] Page source does not contain expected '/sales/lead/' text. Verify if the page loaded correctly.")

            profiles = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/sales/lead/')]")
            print(f"[INFO] Found {len(profiles)} profile link elements on Page {page}.")

            for profile in profiles:
                link = profile.get_attribute("href")
                # Add check for previously_scraped to avoid duplicates
                if link and "linkedin.com" in link and link not in profile_links and link not in previously_scraped:
                    full_link = "https://www.linkedin.com" + link if link.startswith("/sales/lead/") else link
                    profile_links.append(full_link)
                    if len(profile_links) >= MAX_PROFILES:
                        break

            if len(profile_links) >= MAX_PROFILES:
                break

            if len(profile_links) == 0:
                print("[WARNING] No profiles found on this page. Refreshing and retrying...")
                self.driver.refresh()
                time.sleep(10)

            # Try multiple different selectors for the next button
            next_button_found = False
            
            # List of possible XPath selectors for the next button
            next_button_selectors = [
                "//button[contains(@class, 'artdeco-pagination__button--next')]",
                "//li[contains(@class, 'artdeco-pagination__button--next')]/button",
                "//button[@aria-label='Next']",
                "//button[contains(text(), 'Next')]",
                "//span[contains(@class, 'artdeco-button__text') and text()='Next']/parent::button"
            ]
            
            for selector in next_button_selectors:
                next_buttons = self.driver.find_elements(By.XPATH, selector)
                if next_buttons and next_buttons[0].is_enabled():
                    try:
                        # Try scrolling to make the button visible first
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_buttons[0])
                        time.sleep(1)
                        
                        # Take a screenshot before clicking
                        take_debug_screenshot(self.driver, f"page_{page}_next_button_found")
                        
                        next_buttons[0].click()
                        page += 1
                        # Update the last page in history
                        if self.current_url:
                            self.scrape_history[self.current_url]['last_page'] = page
                            self._save_scrape_history()
                        # Add random delay after clicking next page button
                        time.sleep(5 + random.uniform(1, 3))
                        next_button_found = True
                        break
                    except Exception as e:
                        print(f"[WARNING] Error clicking next button with selector {selector}: {e}")
            
            if not next_button_found:
                try:
                    # Last resort: try JavaScript approach to go to next page
                    print("[INFO] Trying JavaScript pagination approach...")
                    self.driver.execute_script("document.querySelector('button.artdeco-pagination__button--next').click();")
                    page += 1
                    if self.current_url:
                        self.scrape_history[self.current_url]['last_page'] = page
                        self._save_scrape_history()
                    time.sleep(5 + random.uniform(1, 3))
                except Exception as e:
                    print("[INFO] No more pages or pagination failed. Breaking loop.")
                    break

        print(f"[OK] Extracted {len(profile_links)} profile links in total.")
        
        # Save the newly found profile links to avoid duplicates in future runs
        if profile_links:
            self.save_profile_links(profile_links)
        
        return profile_links[:MAX_PROFILES]
    
    def scrape_profiles(self, profile_links):
        """Visits each profile and extracts details including name, title, company, email, and website."""
        leads = []
        
        # Apply retry configuration for failed profiles
        max_retries = RETRY_FAILED_PROFILES if 'RETRY_FAILED_PROFILES' in globals() else 0
        
        for index, profile_url in enumerate(profile_links):
            print(f"[INFO] Visiting Profile {index+1}/{len(profile_links)}: {profile_url}")
            
            retry_count = 0
            success = False
            
            while not success and retry_count <= max_retries:
                if retry_count > 0:
                    print(f"[INFO] Retry attempt {retry_count} for profile {profile_url}")
                
                try:
                    self.driver.get(profile_url)
                    # Apply request timeout
                    if 'REQUEST_TIMEOUT' in globals():
                        wait_time = REQUEST_TIMEOUT
                    else:
                        wait_time = 5
                    time.sleep(wait_time)
                    
                    # Take screenshot if enabled
                    if 'SCREENSHOT_PROFILES' in globals() and SCREENSHOT_PROFILES:
                        take_debug_screenshot(self.driver, f"profile_{index+1}")
                    
                    # Add human-like behavior based on configuration
                    if 'SCROLL_BEHAVIOR' in globals() and SCROLL_BEHAVIOR != "none":
                        self.human_like_scroll()
                    
                    # Extract profile data
                    try:
                        name_elements = self.driver.find_elements(By.XPATH, "//h1[@data-x--lead--name]") or                                    self.driver.find_elements(By.XPATH, "//h1[contains(@class, '_headingText_')]") or                                    self.driver.find_elements(By.XPATH, "//h1[contains(@class, 'profile-info-card__name')]") or                                    self.driver.find_elements(By.XPATH, "//h1")
                        name = name_elements[0].text.strip() if name_elements else "N/A"
                    except Exception as e:
                        print(f"[WARNING] Name extraction error: {e}")
                        name = "N/A"
                    
                    try:
                        title_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'profile-info-card__subtitle')]") or                                     self.driver.find_elements(By.XPATH, "//span[contains(@data-anonymize, 'job-title')]") or                                     self.driver.find_elements(By.XPATH, "//span[contains(@class, '_subtitle_')]") or                                     self.driver.find_elements(By.XPATH, "//span[contains(@class, 't-14 t-black')]")
                        title = title_elements[0].text.strip() if title_elements else "N/A"
                    except Exception as e:
                        print(f"[WARNING] Title extraction error: {e}")
                        title = "N/A"
                    
                    try:
                        company_elements = self.driver.find_elements(By.XPATH, "//a[contains(@data-anonymize, 'company-name')]") or                                       self.driver.find_elements(By.XPATH, "//a[contains(@href, '/sales/company/')]") or                                       self.driver.find_elements(By.XPATH, "//a[contains(@href, '/company/')]") or                                       self.driver.find_elements(By.XPATH, "//div[contains(@class, 'profile-info-card__company-name')]")
                        company = company_elements[0].text.strip() if company_elements else "N/A"
                    except Exception as e:
                        print(f"[WARNING] Company extraction error: {e}")
                        company = "N/A"
                    
                    email = extract_email(self.driver)
                    website = extract_website(self.driver)

                    try:
                        location_elements = self.driver.find_elements(
                            By.XPATH,
                            "//div[contains(@class, 'DBrSNqSibpNQelWwoJTqVASHhrvlEGCmad')]//div[not(contains(., 'connections'))]"
                        )
                        location = location_elements[0].text.strip() if location_elements else "N/A"
                    except Exception as e:
                        print(f"[WARNING] Location extraction error: {e}")
                        location = "N/A"
                    
                    profile_data = {
                        "Name": name,
                        "Title": title,
                        "Company": company,
                        "Location": location,
                        "Profile URL": profile_url,
                        "Email": email,
                        "Website": website
                    }
                    
                    # Add LinkedIn URL if extraction is enabled - this is OPTIONAL
                    if 'extract_linkedin_url' in dir(self):
                        linkedin_url = self.extract_linkedin_url()
                        if linkedin_url:
                            profile_data["LinkedIn URL"] = linkedin_url
                    
                    leads.append(profile_data)
                    success = True
                    
                except Exception as e:
                    print(f"[WARNING] Error scraping profile: {e}")
                    if retry_count < max_retries:
                        retry_count += 1
                        delay = RETRY_DELAY if 'RETRY_DELAY' in globals() else 5
                        print(f"[INFO] Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print(f"[WARNING] Skipping profile after {retry_count} failed attempts")
                        break
            
            # Add delay between profiles (with randomization if configured)
            base_delay = DELAY_BETWEEN_REQUESTS
            if 'ADD_RANDOM_DELAYS' in globals() and ADD_RANDOM_DELAYS:
                delay = base_delay + random.uniform(0.5, 2)
            else:
                delay = base_delay
                
            # Adjust based on scraping speed setting
            if 'SCRAPING_SPEED' in globals():
                if SCRAPING_SPEED == "slow":
                    delay *= 1.5
                elif SCRAPING_SPEED == "fast":
                    delay *= 0.7
                    
            time.sleep(delay)
            
        # Process the extracted leads based on settings
        if 'DEDUPLICATE_RESULTS' in globals() and DEDUPLICATE_RESULTS and leads:
            # Remove duplicates based on profile URL
            unique_urls = set()
            unique_leads = []
            for lead in leads:
                if lead["Profile URL"] not in unique_urls:
                    unique_urls.add(lead["Profile URL"])
                    unique_leads.append(lead)
            
            print(f"[INFO] Removed {len(leads) - len(unique_leads)} duplicate profiles")
            leads = unique_leads
            
        return leads
    
    def save_to_csv(self, leads):
        """Save leads to CSV file with configuration options applied."""
        if not leads:
            print("[WARNING] No leads to save")
            return
        
        # Apply output format settings
        filename_prefix = "linkedin_leads"
        timestamp = ""
        if 'INCLUDE_TIMESTAMP' in globals() and INCLUDE_TIMESTAMP:
            timestamp = f"_{time.strftime('%Y%m%d_%H%M%S')}"
        
        output_format = OUTPUT_FORMAT if 'OUTPUT_FORMAT' in globals() else "csv"
        
        output_path = f"output/{filename_prefix}{timestamp}"
        
        # Apply data normalization if enabled
        for lead in leads:
            # Company name normalization
            if 'NORMALIZE_COMPANY_NAMES' in globals() and NORMALIZE_COMPANY_NAMES:
                lead["Company"] = self._normalize_company_name(lead["Company"])
            
            # Job title normalization
            if 'NORMALIZE_JOB_TITLES' in globals() and NORMALIZE_JOB_TITLES:
                lead["Title"] = self._normalize_job_title(lead["Title"])
            
            # Remove emoji from all text fields if enabled
            if 'REMOVE_EMOJI' in globals() and REMOVE_EMOJI:
                for key, value in lead.items():
                    if isinstance(value, str):
                        lead[key] = remove_emoji(value)
        
        if output_format == "csv":
            output_file = f"{output_path}.csv"
            delimiter = CSV_DELIMITER if 'CSV_DELIMITER' in globals() else ","
            
            df = pd.DataFrame(leads)
            df.to_csv(output_file, index=False, sep=delimiter)
            
        elif output_format == "json":
            output_file = f"{output_path}.json"
            with open(output_file, 'w') as f:
                json.dump(leads, f, indent=2)
                
        elif output_format == "excel":
            output_file = f"{output_path}.xlsx"
            df = pd.DataFrame(leads)
            df.to_excel(output_file, index=False)
        
        print(f"[OK] Leads saved to {output_file}")
        
        # Archive old results if enabled
        if 'ARCHIVE_OLD_RESULTS' in globals() and ARCHIVE_OLD_RESULTS:
            self._archive_old_results()
    
    def _normalize_company_name(self, name):
        """Normalize company name based on common patterns."""
        if not name or name == "N/A":
            return name
            
        # Remove common suffixes
        suffixes = [" Inc", " LLC", " Ltd", " Limited", " Corp", " Corporation", " Co", " Company"]
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                
        return name.strip()
    
    def _normalize_job_title(self, title):
        """Normalize job titles for consistency."""
        if not title or title == "N/A":
            return title
            
        # Standardize common titles
        title_map = {
            "CEO": "Chief Executive Officer",
            "CTO": "Chief Technology Officer",
            "CFO": "Chief Financial Officer",
            "COO": "Chief Operating Officer",
            "CMO": "Chief Marketing Officer"
        }
        
        for abbr, full in title_map.items():
            if title.upper() == abbr:
                return full
                
        return title
    
    def _archive_old_results(self):
        """Archive old result files to maintain folder cleanliness."""
        if 'MAX_ARCHIVES_TO_KEEP' not in globals():
            return
            
        try:
            output_dir = "output"
            prefix = "linkedin_leads"
            
            # Get all matching files
            files = [f for f in os.listdir(output_dir) 
                    if f.startswith(prefix) and os.path.isfile(os.path.join(output_dir, f))]
            
            # Sort by modification time (oldest first)
            files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
            
            # If we have more than the limit, move the oldest ones to archive
            if len(files) > MAX_ARCHIVES_TO_KEEP:
                archive_dir = os.path.join(output_dir, "archives")
                os.makedirs(archive_dir, exist_ok=True)
                
                for old_file in files[:-MAX_ARCHIVES_TO_KEEP]:
                    src_path = os.path.join(output_dir, old_file)
                    dst_path = os.path.join(archive_dir, old_file)
                    os.rename(src_path, dst_path)
                    print(f"[INFO] Archived old result file: {old_file}")
        except Exception as e:
            print(f"[WARNING] Error during archiving old results: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Save the final scrape history before quitting
            self._save_scrape_history()
            self.driver.quit()
            print("[OK] Browser closed")
        except Exception as e:
            print(f"[WARNING] Error closing browser: {e}")

    def extract_linkedin_url(self):
        """Extract LinkedIn profile URL by clicking the three dots menu button in the profile header."""
        try:
            print("  - Attempting to extract LinkedIn profile URL...")
            
            # Create a WebDriverWait instance
            wait = WebDriverWait(self.driver, 10)
            
            # Take screenshot before attempting extraction
            take_debug_screenshot(self.driver, "before_url_extraction")
            
            # Target the exact three-dots button in the header section from the HTML
            three_dots_button = None
            
            # Very specific selectors based on the HTML structure provided
            button_selectors = [
                # Most specific selector using the data attribute
                "//button[@data-x--lead-actions-bar-overflow-menu]",
                
                # Target by aria-label
                "//button[@aria-label='Open actions overflow menu']",
                
                # Target by class - specific to the overflow menu in the profile header
                "//button[contains(@class, '_overflow-menu--trigger_')]",
                
                # Target by the specific SVG path (three dots icon)
                "//button[.//svg//path[contains(@d, 'M3 9.5A1.5 1.5 0 114.5 8')]]",
                
                # Target by location in the header section
                "//section[contains(@class, '_header_')]//button[contains(@class, '_tertiary_') and contains(@class, '_circle_')]"
            ]
            
            # Try each selector
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    if buttons:
                        three_dots_button = buttons[0]
                        print(f"  - Found three dots button using selector: {selector}")
                        break
                except:
                    continue
            
            # If we found the three dots button, click it
            if three_dots_button:
                # Take a screenshot of the button
                take_debug_screenshot(self.driver, "three_dots_button")
                
                # Click the button to open the dropdown menu
                three_dots_button.click()
                print("  - Clicked three dots button")
                
                # Wait for the dropdown menu to appear
                time.sleep(1.5)
                
                # Take a screenshot after clicking
                take_debug_screenshot(self.driver, "after_three_dots_click")
                
                # Find and click the "Copy LinkedIn.com URL" option - it's the 3rd option in the dropdown
                # Look for the specific dropdown menu container
                dropdown_items = None
                
                # Try multiple approaches to find dropdown items
                try:
                    # First try using the specific menu ID from the HTML
                    menu_id = three_dots_button.get_attribute("id")
                    if menu_id:
                        menu_container_id = f"hue-menu-{menu_id}"
                        dropdown_items = self.driver.find_elements(By.XPATH, f"//div[@id='{menu_container_id}']//li")
                        print(f"  - Found dropdown menu by ID: {menu_container_id}")
                except:
                    pass
                    
                # If that didn't work, try more general dropdown selectors
                if not dropdown_items or len(dropdown_items) == 0:
                    dropdown_items = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'artdeco-dropdown__content-wrapper')]//li")
                    print("  - Found dropdown items using general selector")
                
                if dropdown_items and len(dropdown_items) >= 3:
                    # Use the 3rd item (index 2 - it's zero-indexed)
                    copy_url_option = dropdown_items[2]  # 3rd item
                    
                    # Take a screenshot before clicking the copy option
                    take_debug_screenshot(self.driver, "copy_url_option")
                    
                    # Click the option
                    copy_url_option.click()
                    print("  - Clicked 3rd dropdown option (LinkedIn.com URL)")
                    
                    # Short wait for the clipboard operation
                    time.sleep(1)
                    
                    # Extract URL from page source
                    page_source = self.driver.page_source
                    url = extract_linkedin_profile_url(page_source)
                    
                    if url:
                        print(f"  - Successfully extracted LinkedIn URL: {url}")
                        return url
                    else:
                        print("  - URL not found in page source after clicking 3rd option")
                else:
                    print(f"  - Dropdown menu not found or has insufficient items: {len(dropdown_items) if dropdown_items else 0} items")
            
            # Fallback to direct extraction from page source
            print("  - Falling back to extraction from page source...")
            page_source = self.driver.page_source
            url = extract_linkedin_profile_url(page_source)
            
            if url:
                print(f"  - Fallback method: found LinkedIn URL: {url}")
                return url
            
            print("  - Failed to extract LinkedIn profile URL")
            return None
            
        except Exception as e:
            print(f"[WARNING] Error in LinkedIn URL extraction: {e}")
            take_debug_screenshot(self.driver, "linkedin_url_extraction_error")
            return None