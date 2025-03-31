"""
Helper functions for the LinkedIn Sales Navigator Scraper
"""
import re
import time
import os
from selenium.webdriver.common.by import By
import unicodedata

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

def extract_linkedin_profile_url(page_source):
    """Extract LinkedIn profile URL from page source using regex patterns."""
    try:
        # Look for public LinkedIn profile URLs in the format linkedin.com/in/username
        url_patterns = [
            r'https://www\.linkedin\.com/in/[a-zA-Z0-9\-_%]+/?',  # Standard format
            r'https://\w+\.linkedin\.com/in/[a-zA-Z0-9\-_%]+/?',  # Country-specific LinkedIn
            r'linkedin\.com/in/[a-zA-Z0-9\-_%]+/?'                # URL without protocol
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                # Filter out URLs that are likely not profile URLs
                profile_matches = [u for u in matches if '/in/' in u]
                if profile_matches:
                    # Ensure URL has https:// prefix
                    url = profile_matches[0]
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
                    
        return None
    except Exception as e:
        print(f"[WARNING] Error extracting LinkedIn profile URL via regex: {e}")
        return None

def remove_emoji(text):
    """Remove emoji characters from text."""
    if not text:
        return text
        
    # Method 1: Using regex to remove emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+", flags=re.UNICODE
    )
    
    text = emoji_pattern.sub(r'', text)
    
    # Method 2: Remove characters categorized as emoticons by unicodedata
    cleaned_text = ""
    for char in text:
        if not (unicodedata.category(char) == 'So' or  # Symbol, Other
                unicodedata.category(char) == 'Cn'):   # Not assigned
            cleaned_text += char
    
    return cleaned_text.strip()
