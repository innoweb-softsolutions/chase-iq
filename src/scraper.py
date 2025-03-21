"""
LinkedIn Sales Navigator Scraper - Core Scraping Logic
"""
import os
import pickle
import time
import undetected_chromedriver as uc
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import logging

from config.config import *
from src.utils.helpers import take_debug_screenshot, extract_email, extract_website

class LinkedInScraper:
    """LinkedIn Sales Navigator Scraper Class"""
    
    def __init__(self):
        """Initialize the scraper with browser settings."""
        self.setup_browser()
        
    def setup_browser(self):
        """Set up the undetected Chrome browser."""
        options = uc.ChromeOptions()
        options.headless = HEADLESS_MODE
        options.add_argument(f"user-agent={UserAgent().random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        self.driver = uc.Chrome(options=options)
        
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
    
    def get_profile_links(self):
        """Extract LinkedIn lead profile URLs from Sales Navigator search results."""
        profile_links = []
        page = 1

        while page <= 1 and len(profile_links) < MAX_PROFILES:
            print(f"[INFO] Extracting Profile Links from Page {page}...")

            # Scroll several times to trigger lazy-loading.
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
                if link and "linkedin.com" in link and link not in profile_links:
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
                    time.sleep(5)
                except Exception as e:
                    print("[WARNING] Error clicking next button:", e)
                    break
            else:
                print("[INFO] No more pages.")
                break

        print(f"[OK] Extracted {len(profile_links)} profile links in total.")
        return profile_links[:MAX_PROFILES]
    
    def scrape_profiles(self, profile_links):
        """Visits each profile and extracts details including name, title, company, email, and website."""
        leads = []
        for index, profile_url in enumerate(profile_links):
            print(f"[INFO] Visiting Profile {index+1}/{len(profile_links)}: {profile_url}")
            try:
                self.driver.get(profile_url)
                time.sleep(5)  # Give page time to load
                
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
            time.sleep(DELAY_BETWEEN_REQUESTS)
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
            self.driver.quit()
            print("[OK] Browser closed")
        except Exception as e:
            print(f"[WARNING] Error closing browser: {e}")
