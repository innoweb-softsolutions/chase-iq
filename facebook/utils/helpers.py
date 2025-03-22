import re
import os
import time
import logging
from urllib.parse import urlparse

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def get_latest_csv_file(directory="output"):
    """Get the latest CSV file from the output directory."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return None
    
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    if not csv_files:
        return None
    
    # Sort by creation time, newest first
    latest_file = max(csv_files, key=lambda f: os.path.getctime(os.path.join(directory, f)))
    return os.path.join(directory, latest_file)

def extract_domain_from_url(url):
    """Extract domain from a URL."""
    if not url:
        return None
    
    # Handle URLs without protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove 'www.' if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from URL {url}: {e}")
        return None

def extract_domain_from_company(company):
    """Create a domain from a company name."""
    if not company or company.lower() == 'n/a':
        return None
        
    # Clean up company name
    company = company.lower()
    company = re.sub(r'\s+(inc|llc|ltd|corp|co)\.?$', '', company)
    company = re.sub(r'[^\w\s]', '', company)
    company = company.strip().replace(' ', '')
    
    if company:
        return f"{company}.com"
        
    return None

def extract_name_parts(name):
    """Extract first and last name from a full name."""
    if not name:
        return None, None
        
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    
    first_name = parts[0]
    last_name = parts[-1]
    
    return first_name, last_name

def safe_request(func, *args, max_retries=3, delay=2, **kwargs):
    """Make a request with retries and error handling."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))  # Increasing delay
            else:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                raise