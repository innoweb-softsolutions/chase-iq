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

from config.config import *
from src.utils.helpers import take_debug_screenshot, extract_email, extract_website

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
        options.add_argument(f"user-agent={UserAgent().random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        self.driver = uc.Chrome(options=options)
        
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
        """Check if URL was previously scraped and prompt user for action."""
        self.current_url = url
        
        if url in self.scrape_history:
            last_page = self.scrape_history[url].get('last_page', 1)
            last_scraped = self.scrape_history[url].get('last_scraped', 'unknown date')
            
            print(f"[INFO] This URL was previously scraped (reached page {last_page}) on {last_scraped}.")
            
            while True:
                choice = input("[ACTION] Do you want to start from scratch or continue where you left off? (scratch/continue): ").lower().strip()
                
                if choice in ['scratch', 's']:
                    # Reset the history for this URL
                    self.scrape_history[url] = {
                        'last_page': 1,
                        'last_scraped': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return 1  # Start from page 1
                    
                elif choice in ['continue', 'c']:
                    self.scrape_history[url]['last_scraped'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    return last_page  # Continue from last page
                    
                else:
                    print("[WARNING] Invalid choice. Please enter 'scratch' or 'continue'.")
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
        try:
            # Get current scroll height
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Number of scroll steps (random)
            steps = random.randint(3, 5)
            
            for i in range(steps):
                # Random scroll distance (percentage of page)
                scroll_percent = random.uniform(0.1, 0.3)
                scroll_y = int(scroll_height * scroll_percent)
                
                # Scroll down with random pause
                self.driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                time.sleep(random.uniform(0.5, 1.5))
                
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

        # Changed from page <= 1 to page <= 20
        while page <= 5 and len(profile_links) < MAX_PROFILES:
            print(f"[INFO] Extracting Profile Links from Page {page}...")

            # Add human-like scrolling before extracting profiles
            self.human_like_scroll()
            
            # Original scrolling code - keep for consistency
            for _ in range(7):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            time.sleep(5)

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

            next_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'artdeco-pagination__button--next')]")
            if next_buttons and next_buttons[0].is_enabled():
                try:
                    next_buttons[0].click()
                    page += 1
                    # Update the last page in history
                    if self.current_url:
                        self.scrape_history[self.current_url]['last_page'] = page
                        self._save_scrape_history()
                    # Add random delay after clicking next page button
                    time.sleep(5 + random.uniform(1, 3))
                except Exception as e:
                    print("[WARNING] Error clicking next button:", e)
                    break
            else:
                print("[INFO] No more pages.")
                break

        print(f"[OK] Extracted {len(profile_links)} profile links in total.")
        
        # Save the newly found profile links to avoid duplicates in future runs
        if profile_links:
            self.save_profile_links(profile_links)
        
        return profile_links[:MAX_PROFILES]
    
    def scrape_profiles(self, profile_links):
        """Visits each profile and extracts details including name, title, company, email, and website."""
        leads = []
        for index, profile_url in enumerate(profile_links):
            print(f"[INFO] Visiting Profile {index+1}/{len(profile_links)}: {profile_url}")
            try:
                self.driver.get(profile_url)
                time.sleep(5)  # Give page time to load
                
                # Add some human-like behavior
                self.human_like_scroll()
                
                # Updated name extraction for the new Sales Navigator HTML structure
                try:
                    # Target the specific h1 with data-x--lead--name attribute
                    name_elements = self.driver.find_elements(By.XPATH, "//h1[@data-x--lead--name]") or                                    self.driver.find_elements(By.XPATH, "//h1[contains(@class, '_headingText_')]") or                                    self.driver.find_elements(By.XPATH, "//h1[contains(@class, 'profile-info-card__name')]") or                                    self.driver.find_elements(By.XPATH, "//h1")
                    name = name_elements[0].text.strip() if name_elements else "N/A"
                except Exception as e:
                    print(f"[WARNING] Name extraction error: {e}")
                    name = "N/A"
                
                # Updated title extraction
                try:
                    # Try various possible selectors for the job title
                    title_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'profile-info-card__subtitle')]") or                                     self.driver.find_elements(By.XPATH, "//span[contains(@data-anonymize, 'job-title')]") or                                     self.driver.find_elements(By.XPATH, "//span[contains(@class, '_subtitle_')]") or                                     self.driver.find_elements(By.XPATH, "//span[contains(@class, 't-14 t-black')]")
                    title = title_elements[0].text.strip() if title_elements else "N/A"
                except Exception as e:
                    print(f"[WARNING] Title extraction error: {e}")
                    title = "N/A"
                
                # Updated company extraction
                try:
                    # Try various possible selectors for the company name
                    company_elements = self.driver.find_elements(By.XPATH, "//a[contains(@data-anonymize, 'company-name')]") or                                       self.driver.find_elements(By.XPATH, "//a[contains(@href, '/sales/company/')]") or                                       self.driver.find_elements(By.XPATH, "//a[contains(@href, '/company/')]") or                                       self.driver.find_elements(By.XPATH, "//div[contains(@class, 'profile-info-card__company-name')]")
                    company = company_elements[0].text.strip() if company_elements else "N/A"
                except Exception as e:
                    print(f"[WARNING] Company extraction error: {e}")
                    company = "N/A"
                    
                email = extract_email(self.driver)
                website = extract_website(self.driver)
                
                # Print extracted data for debugging
                print(f"  - Name: {name}")
                print(f"  - Title: {title}")
                print(f"  - Company: {company}")
                print(f"  - Email: {email}")
                print(f"  - Website: {website}")
                
                leads.append({
                    "Name": name,
                    "Title": title,
                    "Company": company,
                    "Profile URL": profile_url,
                    "Email": email,
                    "Website": website
                })
            except Exception as e:
                print(f"[WARNING] Skipping profile due to error: {e}")
            
            # Add randomization to delay between requests for more human-like behavior
            delay = DELAY_BETWEEN_REQUESTS + random.uniform(0.5, 2)
            time.sleep(delay)
            
        return leads
    
    def save_to_csv(self, leads):
        """Save leads to CSV file."""
        if not leads:
            print("[WARNING] No leads to save")
            return
            
        output_file = f"output/linkedin_leads_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame(leads)
        df.to_csv(output_file, index=False)
        print(f"[OK] Leads saved to {output_file}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Save the final scrape history before quitting
            self._save_scrape_history()
            self.driver.quit()
            print("[OK] Browser closed")
        except Exception as e:
            print(f"[WARNING] Error closing browser: {e}")