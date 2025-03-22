import re
import logging
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup

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
            'real estate expert', 'real estate professional'
        ]
        
        # Check for title patterns: "I am a [title]" or "[name] is a [title]"
        patterns = []
        if name:
            first_name = name.split()[0]
            patterns.append(fr'{first_name} is an? (.+?)(\.|\n|,)')
            patterns.append(fr'{name} is an? (.+?)(\.|\n|,)')
            
        patterns.extend([
            r'I am an? (.+?)(\.|\n|,)',
            r'working as an? (.+?)(\.|\n|,)',
            r'position as an? (.+?)(\.|\n|,)'
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
            'group', 'agency', 'associates', 'brokerage'
        ]
        
        # Check for company patterns
        patterns = []
        if name:
            first_name = name.split()[0]
            patterns.append(fr'{first_name} .* at (.+?)(\.|\n|,)')
            patterns.append(fr'{name} .* at (.+?)(\.|\n|,)')
            
        patterns.extend([
            r'I work.* at (.+?)(\.|\n|,)',
            r'I (?:am with|am employed by|work for) (.+?)(\.|\n|,)',
            r'founder of (.+?)(\.|\n|,)',
            r'owner of (.+?)(\.|\n|,)',
            r'my (?:company|agency|firm|brokerage) (.+?)(\.|\n|,)'
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
        return BeautifulSoup(text, "html.parser").get_text()
    
    @staticmethod
    def format_for_pipeline(facebook_posts):
        """Format Facebook posts to match LinkedIn Sales Navigator pipeline output format."""
        leads = []
        
        for post in facebook_posts:
            # Extract data
            name = post.get('username', 'N/A')
            profile_url = post.get('user_url', 'N/A')
            post_text = DataProcessor.clean_html(post.get('text', ''))
            
            # Extract additional information
            website = post.get('link') or DataProcessor.extract_website_from_text(post_text)
            title = DataProcessor.extract_title_from_text(post_text, name)
            company = DataProcessor.extract_company_from_text(post_text, name)
            
            # Create lead entry in the expected format
            lead = {
                "Name": name,
                "Title": title,
                "Company": company,
                "Profile URL": profile_url,
                "Email": "N/A",  # Will be filled by email finder
                "Website": website
            }
            
            leads.append(lead)
            
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