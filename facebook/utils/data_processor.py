import re
import logging
import pandas as pd
import os
from datetime import datetime
from bs4 import BeautifulSoup
import traceback

from ..utils.helpers import extract_domain_from_url, extract_name_parts

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process scraped Facebook data and format it for the email finder pipeline."""
    
    @staticmethod
    def extract_website_from_text(text):
        """Extract website links from post text."""
        if not text:
            return None
            
        # Find URLs in text
        url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)(?:[/\w.-]*)*'
        urls = re.findall(url_pattern, text)
        
        if urls:
            # Filter out facebook.com and common social media domains
            social_domains = ['facebook.com', 'fb.com', 'instagram.com', 'twitter.com', 'linkedin.com']
            clean_urls = [url for url in urls if not any(domain in url for domain in social_domains)]
            return clean_urls[0] if clean_urls else None
            
        return None
        
    @staticmethod
    def extract_title_from_text(text, name=None):
        """Extract potential job title from post text using common patterns."""
        if not text:
            return "N/A"
            
        # Common real estate job titles
        real_estate_titles = [
            'realtor', 'real estate agent', 'real estate broker', 'property manager',
            'real estate investor', 'real estate developer', 'mortgage broker', 
            'loan officer', 'real estate consultant', 'real estate coach',
            'real estate expert', 'real estate professional', 'property dealer',
            'property consultant', 'property advisor'
        ]
        
        # Check for title patterns: "I am a [title]" or "[name] is a [title]"
        patterns = []
        if name and name != 'N/A':
            first_name = name.split()[0]
            patterns.append(fr'{first_name} is an? (.+?)(\.|\n|,)')
            patterns.append(fr'{name} is an? (.+?)(\.|\n|,)')
            
        patterns.extend([
            r'I am an? (.+?)(\.|\n|,)',
            r'working as an? (.+?)(\.|\n|,)',
            r'position as an? (.+?)(\.|\n|,)',
            r'I\'m an? (.+?)(\.|\n|,)',
            r'experienced (.+?)(\.|\n|,)',
            r'professional (.+?)(\.|\n|,)',
            r'certified (.+?)(\.|\n|,)'
        ])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Check if the extracted title contains a real estate keyword
                if any(re.search(re_title, title, re.IGNORECASE) for re_title in real_estate_titles):
                    return title
                    
        # Check if any real estate title appears directly in the text
        for title in real_estate_titles:
            if re.search(r'\b' + title + r'\b', text, re.IGNORECASE):
                return title.title()  # Convert to title case
                
        return "N/A"
        
    @staticmethod
    def extract_company_from_text(text, name=None):
        """Extract potential company name from post text using common patterns."""
        if not text:
            return "N/A"
            
        # Common real estate company indicators
        company_indicators = [
            'realty', 'properties', 'real estate', 'homes', 'property management',
            'group', 'agency', 'associates', 'brokerage', 'advisors', 'consultants',
            'estate', 'housing', 'investments', 'developers'
        ]
        
        # Check for company patterns
        patterns = []
        if name and name != 'N/A':
            first_name = name.split()[0]
            patterns.append(fr'{first_name} .* at (.+?)(\.|\n|,)')
            patterns.append(fr'{name} .* at (.+?)(\.|\n|,)')
            
        patterns.extend([
            r'I work.* at (.+?)(\.|\n|,)',
            r'I (?:am with|am employed by|work for) (.+?)(\.|\n|,)',
            r'founder of (.+?)(\.|\n|,)',
            r'owner of (.+?)(\.|\n|,)',
            r'my (?:company|agency|firm|brokerage) (.+?)(\.|\n|,)',
            r'(?:CEO|President|Director|Manager|Broker|Owner) (?:of|at) (.+?)(\.|\n|,)',
            r'(?:joined|work with|representing) (.+?)(\.|\n|,)'
        ])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Check if the extracted company contains a real estate keyword
                if any(re.search(indicator, company, re.IGNORECASE) for indicator in company_indicators):
                    return company
                    
        return "N/A"
    
    @staticmethod
    def clean_html(text):
        """Clean HTML from text."""
        if not text:
            return ""
        try:
            return BeautifulSoup(text, "html.parser").get_text()
        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return text
    
    @staticmethod
    def format_for_pipeline(facebook_posts):
        """Format Facebook posts to match pipeline output format."""
        leads = []
        processed_users = set()  # Track processed users to avoid duplicates
        
        logger.info(f"Processing {len(facebook_posts)} posts to extract leads")
        
        for post in facebook_posts:
            try:
                # Debug the post structure
                logger.debug(f"Processing post: {list(post.keys()) if post else 'Empty post'}")
                
                # Skip posts without useful information
                if not post.get('text') and not post.get('post_text'):
                    logger.debug("Skipping post with no text content")
                    continue
                    
                # Extract username and post text
                username = post.get('username', post.get('user_name', 'N/A'))
                if username == 'N/A':
                    logger.debug("Post has no username, trying to extract from author data")
                    username = post.get('user', {}).get('name', 'N/A') if isinstance(post.get('user'), dict) else 'N/A'
                
                # Skip if we've already processed this user
                if username in processed_users and username != 'N/A':
                    logger.debug(f"Skipping duplicate user: {username}")
                    continue
                    
                # Get profile URL 
                profile_url = post.get('user_url', '')
                if not profile_url:
                    if isinstance(post.get('user'), dict):
                        profile_url = post.get('user', {}).get('link', '')
                        
                    if not profile_url and username != 'N/A':
                        profile_url = f"https://facebook.com/{username}"
                
                # Get post text, trying multiple possible fields
                post_text = post.get('text', post.get('post_text', ''))
                post_text = DataProcessor.clean_html(post_text)
                
                # Debug output to see what data we're getting
                logger.debug(f"Processing post from {username} with text length: {len(post_text)}")
                if len(post_text) > 0:
                    logger.debug(f"Text sample: {post_text[:100]}...")
                
                # Extract additional information
                website = post.get('link') or DataProcessor.extract_website_from_text(post_text)
                title = DataProcessor.extract_title_from_text(post_text, username)
                company = DataProcessor.extract_company_from_text(post_text, username)
                
                # Create lead entry in the expected format
                lead = {
                    "Name": username,
                    "Title": title,
                    "Company": company,
                    "Profile URL": profile_url,
                    "Email": "N/A",  # Will be filled by email finder
                    "Website": website
                }
                
                # Add lead to results
                leads.append(lead)
                logger.debug(f"Added lead: {username}, {title}, {company}")
                
                # Track processed users
                if username != 'N/A':
                    processed_users.add(username)
                    
            except Exception as e:
                logger.error(f"Error processing post: {e}")
                logger.error(traceback.format_exc())
                continue
        
        logger.info(f"Extracted {len(leads)} leads from {len(facebook_posts)} posts")
        return leads
    
    @staticmethod
    def save_to_csv(leads, filename=None):
        """Save leads to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/facebook_leads_{timestamp}.csv"
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save to CSV
        df = pd.DataFrame(leads)
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(leads)} leads to {filename}")
        
        return filename