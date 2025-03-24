"""
Data extractors for Facebook content
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

logger = logging.getLogger(__name__)

class PostExtractor:
    """Extracts data from Facebook posts."""
    
    def __init__(self):
        """Initialize the post extractor."""
        self.max_retries = 3
    
    def extract_post_data(self, post_element, browser, post_id):
        """Extract data from a post element."""
        try:
            # Re-find the element to avoid stale references
            try:
                # First try to access it directly
                post_element.is_displayed()  # Just to check if it's still valid
            except StaleElementReferenceException:
                logger.debug(f"Stale element, cannot process post {post_id}")
                return None
            
            # Extract components with retry mechanism
            username = self._extract_username(post_element)
            profile_url = self._extract_profile_url(post_element)
            post_text = self._extract_post_text(post_element)
            links = self._extract_links(post_element)
            
            # Only create post if we have meaningful content
            if post_text or links:
                post = {
                    'post_id': post_id,
                    'username': username,
                    'user_url': profile_url,
                    'text': post_text.strip() if post_text else "",
                    'link': links[0] if links else None,
                    'links': links
                }
                return post
            
            return None
            
        except StaleElementReferenceException:
            logger.error(f"Stale element reference for post {post_id}")
            return None
        except Exception as e:
            logger.error(f"Error extracting post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _extract_username(self, post_element):
        """Extract the username from a post."""
        username = "Unknown"
        retry_count = 0
        
        # Updated author selectors for 2024 Facebook
        author_selectors = [
            "h3 a", 
            "a[role='link']:not([aria-hidden='true'])",
            "span.x1i10hfl a",                         # Recent profile links
            "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq a", # Profile link class
            "a.x1i10hfl"                              # Common Facebook link class
        ]
        
        while retry_count < self.max_retries and username == "Unknown":
            try:
                for author_selector in author_selectors:
                    try:
                        author_elements = WebDriverWait(post_element, 3).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, author_selector))
                        )
                        
                        for author_el in author_elements:
                            try:
                                if author_el.text and len(author_el.text) > 0:
                                    # Skip common non-author elements
                                    text = author_el.text.lower()
                                    if text in ["like", "comment", "share", "save", "follow"]:
                                        continue
                                        
                                    username = author_el.text
                                    break
                            except StaleElementReferenceException:
                                continue
                            except Exception as e:
                                logger.debug(f"Error extracting author text: {e}")
                                continue
                        
                        if username != "Unknown":
                            break
                            
                    except (TimeoutException, NoSuchElementException):
                        continue
                    except Exception as e:
                        logger.debug(f"Error with author selector {author_selector}: {e}")
                
                if username != "Unknown":
                    break
                    
                retry_count += 1
                if retry_count < self.max_retries:
                    logger.debug(f"Retrying author extraction, attempt {retry_count+1}/{self.max_retries}")
                    time.sleep(1)
                    
            except StaleElementReferenceException:
                retry_count += 1
                if retry_count >= self.max_retries:
                    break
        
        return username
    
    def _extract_profile_url(self, post_element):
        """Extract the profile URL from a post."""
        profile_url = None
        retry_count = 0
        
        # Updated author selectors for 2024 Facebook
        author_selectors = [
            "h3 a", 
            "a[role='link']:not([aria-hidden='true'])",
            "span.x1i10hfl a",                         # Recent profile links
            "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq a", # Profile link class
            "a.x1i10hfl"                              # Common Facebook link class
        ]
        
        while retry_count < self.max_retries and not profile_url:
            try:
                for author_selector in author_selectors:
                    try:
                        author_elements = WebDriverWait(post_element, 3).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, author_selector))
                        )
                        
                        for author_el in author_elements:
                            try:
                                href = author_el.get_attribute("href")
                                if href and "facebook.com" in href:
                                    # Skip reaction links
                                    if "reaction/profile" in href or "comment" in href:
                                        continue
                                    profile_url = href
                                    break
                            except StaleElementReferenceException:
                                continue
                            except Exception as e:
                                logger.debug(f"Error extracting profile URL: {e}")
                                continue
                        
                        if profile_url:
                            break
                            
                    except (TimeoutException, NoSuchElementException):
                        continue
                    except Exception as e:
                        logger.debug(f"Error with author selector for URL {author_selector}: {e}")
                
                if profile_url:
                    break
                    
                retry_count += 1
                if retry_count < self.max_retries:
                    logger.debug(f"Retrying profile URL extraction, attempt {retry_count+1}/{self.max_retries}")
                    time.sleep(1)
                    
            except StaleElementReferenceException:
                retry_count += 1
                if retry_count >= self.max_retries:
                    break
        
        return profile_url
    
    def _extract_post_text(self, post_element):
        """Extract the text content from a post."""
        post_text = ""
        retry_count = 0
        
        # Extract post text with updated selectors
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
        
        while retry_count < self.max_retries and not post_text:
            try:
                for text_selector in text_selectors:
                    try:
                        text_elements = WebDriverWait(post_element, 3).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, text_selector))
                        )
                        
                        for text_el in text_elements:
                            try:
                                if text_el.text and len(text_el.text) > 10:  # Minimum text length
                                    # Skip if it's a common UI text
                                    content = text_el.text.lower()
                                    if content in ["see more", "see less", "view more comments"]:
                                        continue
                                    post_text += text_el.text + "\n"
                            except StaleElementReferenceException:
                                continue
                            except Exception as e:
                                logger.debug(f"Error extracting text content: {e}")
                        
                        if post_text:
                            break
                    
                    except (TimeoutException, NoSuchElementException):
                        continue
                    except Exception as e:
                        logger.debug(f"Error with text selector {text_selector}: {e}")
                
                if post_text:
                    break
                    
                retry_count += 1
                if retry_count < self.max_retries:
                    logger.debug(f"Retrying text extraction, attempt {retry_count+1}/{self.max_retries}")
                    time.sleep(1)
                    
            except StaleElementReferenceException:
                retry_count += 1
                if retry_count >= self.max_retries:
                    break
        
        return post_text
    
    def _extract_links(self, post_element):
        """Extract links from a post that aren't Facebook internal links."""
        links = []
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                link_elements = WebDriverWait(post_element, 3).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href]:not([role='button']):not([href*='facebook.com']):not([href*='fb.com'])"))
                )
                
                for link_el in link_elements:
                    try:
                        href = link_el.get_attribute("href")
                        if href and "facebook.com" not in href and "fb.com" not in href:
                            links.append(href)
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        logger.debug(f"Error extracting link: {e}")
                
                break  # Successfully got links or there are none
                    
            except (TimeoutException, NoSuchElementException):
                # No links found, that's ok
                break
            except StaleElementReferenceException:
                retry_count += 1
                if retry_count >= self.max_retries:
                    break
            except Exception as e:
                logger.debug(f"Error finding links: {e}")
                break
        
        return links