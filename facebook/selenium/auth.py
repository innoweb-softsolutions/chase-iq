"""
Authentication and login handling for Facebook scraping
"""
import time
import logging
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class FacebookAuthenticator:
    """Handles Facebook authentication and login."""
    
    def __init__(self, browser_manager, email=None, password=None):
        """Initialize the authenticator with browser and credentials."""
        self.browser_manager = browser_manager
        self.email = email
        self.password = password
        self.logged_in = False
    
    def login(self):
        """Attempt to log in to Facebook using cookies or credentials."""
        browser = self.browser_manager.setup_browser()
        
        # First try to use saved cookies
        if self.browser_manager.load_cookies():
            # Navigate to Facebook to verify login status
            browser.get("https://www.facebook.com/")
            time.sleep(5)
            
            # Take a screenshot for debugging
            self.browser_manager.take_screenshot("facebook_login_attempt.png")
            
            # Check login status using multiple indicators
            login_indicators = [
                "login" not in browser.current_url.lower(),
                len(browser.find_elements(By.XPATH, "//div[@role='navigation']")) > 0,
                len(browser.find_elements(By.XPATH, "//div[@aria-label='Facebook']")) > 0,
                len(browser.find_elements(By.XPATH, "//div[contains(@aria-label, 'Your profile')]")) > 0,
                len(browser.find_elements(By.XPATH, "//div[contains(@class, 'x1n2onr6')]")) > 0,  # Common FB container
            ]
            
            logger.debug(f"Login indicators: {login_indicators}")
            
            if any(login_indicators):
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
            browser.get("https://www.facebook.com/")
            
            # Handle cookie consent if present
            self._handle_cookie_consent(browser)
            
            # Perform login with credentials
            login_success = self._perform_login(browser)
            
            if login_success:
                self.logged_in = True
                # Save cookies for future sessions
                self.browser_manager.save_cookies()
                
            return login_success
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _handle_cookie_consent(self, browser):
        """Handle cookie consent dialogs if they appear."""
        try:
            cookie_buttons = WebDriverWait(browser, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button[data-cookiebanner='accept_button']"))
            )
            for button in cookie_buttons:
                if "Accept" in button.text or "Accept All" in button.text:
                    button.click()
                    logger.debug("Accepted cookies")
                    break
        except (TimeoutException, NoSuchElementException):
            logger.debug("No cookie banner found or it was already handled")
    
    def _perform_login(self, browser):
        """Enter credentials and submit the login form."""
        try:
            # Try multiple selectors for the email field
            selectors = [
                (By.ID, "email"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[name='email']"),
                (By.CSS_SELECTOR, "input[type='text']")
            ]
            
            email_field = None
            for selector_type, selector_value in selectors:
                try:
                    email_field = WebDriverWait(browser, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    if email_field:
                        break
                except:
                    continue
            
            if not email_field:
                logger.error("Could not find email field")
                # Take screenshot to see the page
                browser.save_screenshot("login_form_not_found.png")
                logger.info("Screenshot saved as login_form_not_found.png")
                return False
            
            # Similarly find password field with multiple approaches
            password_selectors = [
                (By.ID, "pass"),
                (By.NAME, "pass"),
                (By.CSS_SELECTOR, "input[name='pass']"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]
            
            password_field = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = WebDriverWait(browser, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            # Input credentials
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(1)  # Small delay between fields
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)  # Small delay before submission
            
            # Find and click login button with multiple approaches
            login_button = None
            login_button_selectors = [
                (By.NAME, "login"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Log In')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]")
            ]
            
            for selector_type, selector_value in login_button_selectors:
                try:
                    login_button = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    if login_button:
                        break
                except:
                    continue
            
            if not login_button:
                logger.error("Could not find login button")
                return False
            
            login_button.click()
            
            # Wait for login to complete
            time.sleep(7)
            
            # Save screenshot for debugging
            browser.save_screenshot("facebook_login_attempt.png")
            logger.info("Login attempt screenshot saved to facebook_login_attempt.png")
            
            # Check for login issues or security checkpoints
            if ("checkpoint" in browser.current_url.lower() or 
                "login" in browser.current_url.lower()):
                
                logger.warning("Facebook security checkpoint detected or login failed")
                logger.info("Waiting for manual login - Please complete the login in the browser window")
                
                # Extended wait for manual intervention
                manual_wait = 120  # 2 minutes for manual login
                logger.info(f"Waiting {manual_wait} seconds for manual login")
                time.sleep(manual_wait)
                
                # Check login status again
                if "login" not in browser.current_url.lower():
                    logger.info("Manual login appears successful")
                    return True
                else:
                    logger.error("Manual login also failed")
                    return False
            
            # Check login success using multiple indicators
            login_success_indicators = [
                "login" not in browser.current_url.lower(),
                len(browser.find_elements(By.XPATH, "//div[@role='navigation']")) > 0,
                len(browser.find_elements(By.XPATH, "//div[@aria-label='Facebook']")) > 0,
                len(browser.find_elements(By.XPATH, "//div[contains(@aria-label, 'Your profile')]")) > 0,
                len(browser.find_elements(By.XPATH, "//div[contains(@class, 'x1n2onr6')]")) > 0,  # Common FB container
            ]
            
            logger.debug(f"Login success indicators: {login_success_indicators}")
            
            if any(login_success_indicators):
                logger.info("Login successful")
                return True
            else:
                logger.error("Couldn't find post-login elements")
                logger.error("Login unsuccessful, still on login page or encountered an error")
                return False
                
        except Exception as e:
            logger.error(f"Failed to log in: {e}")
            logger.error(traceback.format_exc())
            return False