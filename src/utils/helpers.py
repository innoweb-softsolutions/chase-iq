"""
Helper functions for the LinkedIn Sales Navigator Scraper
"""
import re
import time
import os
from selenium.webdriver.common.by import By

def take_debug_screenshot(driver, name="debug_screenshot"):
    """Take a screenshot for debugging purposes."""
    try:
        os.makedirs("output/screenshots", exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"output/screenshots/{name}_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"[DEBUG] Debug screenshot saved as {filename}")
        return filename
    except Exception as e:
        print(f"[ERROR] Failed to take debug screenshot: {e}")
        return None

def extract_email(driver):
    """Attempts to extract an email from the current profile page."""
    try:
        email_elements = driver.find_elements(By.XPATH, "//a[starts-with(@href, 'mailto:')]")
        for element in email_elements:
            href = element.get_attribute("href")
            if href and href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                return email
    except Exception as e:
        print("[WARNING] Email extraction error (mailto):", e)
    
    try:
        page_source = driver.page_source
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", page_source)
        if emails:
            return emails[0]
    except Exception as e:
        print("[WARNING] Email extraction error (regex):", e)
    
    return "N/A"

def extract_website(driver):
    """Attempts to extract a website URL from the current profile page."""
    try:
        # First, check if we need to click a "Contact info" tab or section to reveal website
        contact_tabs = driver.find_elements(By.XPATH, 
            "//h2[contains(text(), 'Contact information') or contains(@class, '_header_') and contains(text(), 'Contact')]")
        
        if contact_tabs:
            # If we found a contact information section, look for website links within it
            print("  - Found Contact information section")
            
            # Look for website links specifically with the data-anonymize="url" attribute
            website_elements = driver.find_elements(By.XPATH, 
                "//a[@data-anonymize='url' or contains(@href, 'http') and not(contains(@href, 'linkedin.com')) and not(contains(@href, 'mailto:'))]")
            
            for element in website_elements:
                href = element.get_attribute("href")
                text = element.text.strip()
                
                if href and "linkedin.com" not in href and "mailto:" not in href:
                    print(f"  - Found website: {text} (URL: {href})")
                    # Clean up the URL if needed
                    if "?" in href and ("url=" in href or "redirect=" in href):
                        # Extract actual URL from redirect URL
                        match = re.search(r'(?:url=|redirect=)(https?://[^&]+)', href)
                        if match:
                            return match.group(1)
                    return href
    except Exception as e:
        print(f"[WARNING] Contact info website extraction error: {e}")
    
    # Fallback - try standard website extraction methods
    try:
        # Look for any website elements across the page
        website_elements = driver.find_elements(By.XPATH, 
            "//a[contains(@href, 'http') and not(contains(@href, 'linkedin.com')) and not(contains(@href, 'mailto:'))]")
        
        for element in website_elements:
            href = element.get_attribute("href")
            if href and "linkedin.com" not in href and "mailto:" not in href:
                if "?" in href and ("url=" in href or "redirect=" in href):
                    match = re.search(r'(?:url=|redirect=)(https?://[^&]+)', href)
                    if match:
                        return match.group(1)
                return href
    except Exception as e:
        print(f"[WARNING] Website extraction error: {e}")
    
    # Last resort - try extracting website from the page source using regex
    try:
        page_source = driver.page_source
        # First, look specifically for www.* patterns in the text
        specific_urls = re.findall(r'www\.[A-Za-z0-9-]+\.[A-Za-z0-9.-]+', page_source)
        for url in specific_urls:
            if "linkedin.com" not in url and len(url) > 5:
                return f"http://{url}"
                
        # Then try more general URL patterns
        general_urls = re.findall(r'https?://(?:www\.)?([A-Za-z0-9-]+\.[A-Za-z0-9.-]+)(?:/[^\s"\'<>)\]]*)?', page_source)
        for url in general_urls:
            if "linkedin.com" not in url and len(url) > 5:
                return f"http://{url}"
    except Exception as e:
        print(f"[WARNING] Website regex extraction error: {e}")
    
    return "N/A"
