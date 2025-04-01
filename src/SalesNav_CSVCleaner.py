import os
import sys
import pandas as pd
import re
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

"Output CSV FILE STORED IN OUTPUT FOLDER"
"INPUT command python SalesNav_CSVCleaner.py ../output/(name).csv "
"Output CSV FILE STORED IN OUTPUT FOLDER"
"INPUT command python SalesNav_CSVCleaner.py ../output/(name).csv "

def clean_name(full_name):
    """Cleans name by removing initials, suffixes, certifications and nicknames."""
    if not full_name or full_name.strip().lower() in {"n/a", "na"}:
        return None, None

    # Remove any non-ASCII characters (to handle encoding issues)
    full_name = re.sub(r'[^\x00-\x7F]+', '', full_name)
    
    # Remove nicknames in quotes
    full_name = re.sub(r'["\'][\w\s]+["\']', '', full_name)
    
    # Split into words
    words = full_name.replace(",", "").split()  # Remove commas before splitting

    # Remove initials (single letters with or without a dot)
    words = [word for word in words if not re.fullmatch(r"[A-Z]\.?$", word)]
    
    # Expanded list of common suffixes and professional certifications to remove
    suffixes = {
        # Academic and professional degrees
        "Jr", "Sr", "II", "III", "IV", "MD", "PhD", "RN", "BSN", "MBA", 
        "CPA", "CFA", "CWS", "CFP", "DDS", "Esq", "JD", "MSA", "MS", "MA",
        # Business titles
        "CEO", "CFO", "COO", "CTO", "CMO", "CHRO", "CIO", "CCO",
        "President", "VP", "Director", "Manager", "Partner", "Associate",
        # Real estate specific
        "REALTOR", "REALTORÂ®", "ARM", "ABR", "GRI", "CRS", "SRS"
    }

    # Filter out credential patterns (all caps with possible hyphens, like MSGB-LMOC)
    words = [word for word in words if not re.fullmatch(r"[A-Z0-9\-]+$", word) or word in {"I", "II", "III", "IV", "V"}]
    
    # Remove suffixes (case-insensitive comparison)
    words = [word for word in words if word.upper() not in {s.upper() for s in suffixes}]

    # Ensure we have at least two words left for first and last name
    if len(words) < 2:
        return None, None  # If only one word remains, it's not a full name

    # Always return the first two remaining words as first and last name
    return words[0], words[1]

def extract_domain(website, company):
    """Extracts a valid business domain from the website URL or company name."""
    
    # Expanded list of domains to ignore
    invalid_domains = {
        # Search engines
        "google.com", "bing.com", "yahoo.com", "duckduckgo.com",
        # Social media
        "twitter.com", "youtube.com", "facebook.com", "instagram.com",
        "linkedin.com", "tiktok.com", "pinterest.com",
        # Link aggregators
        "linktr.ee", "linkin.bio", "bit.ly", "t.co",
        # Free blogging/hosting
        "wordpress.com", "blogspot.com", "wix.com", "squarespace.com",
        "webflow.io", "medium.com", "tumblr.com",
        # Invalid URL parts
        "http", "https"
    }

    domain = None  # Default value

    if website and website != "N/A":
        try:
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            parsed_url = urlparse(website)
            domain = parsed_url.netloc or parsed_url.path

            # Remove "www." prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Handle search URLs
            if any(search_domain in domain for search_domain in ["bing.com", "google.com", "yahoo.com"]) and "search" in parsed_url.path:
                domain = None

            # Ignore invalid domains
            if domain in invalid_domains or not domain or domain.count('.') < 1:
                domain = None
                
            # Handle free subdomains of blogging platforms
            if domain and any(domain.endswith(f".{free_domain}") for free_domain in ["wordpress.com", "blogspot.com", "wix.com"]):
                domain = None

        except Exception:
            domain = None
    
    # Extract domain from company name if the website is invalid
    if not domain and company and company != "N/A":
        company = company.lower()
        for suffix in [' inc', ' llc', ' ltd', ' corp', ' group', ' properties', ' realty', ' homes']:
            if company.endswith(suffix):
                company = company[:-len(suffix)]

        company = ''.join(c for c in company if c.isalnum() or c == ' ')
        company = company.strip().replace(' ', '')

        if company:
            return f"{company}.com"
    
    return domain

def is_business_email(email):
    """Check if an email is a business email. Returns True if business, False if personal."""
    personal_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "aol.com"}
    if "@" in email:
        domain = email.split('@')[-1].strip().lower()
        return domain not in personal_domains and "." in domain  # Ensure it’s a valid domain
    return False


def extract_role(title):
    
    executive_roles = {
        "CEO", "CFO", "COO", "Founder", "Co-Founder", "Owner", "Co-Owner",
        "Director", "Vice President", 
        "President", "Chief", "Principal","Chief Executive Officer","Chief Operating Officer",
        "Chief Financial Officer"
    }

    # List of roles to EXCLUDE
    excluded_roles = {"Coordinator", "Assistant", "Specialist", "Analyst", "Representative", "Associate"}

    # Convert title to lowercase for case-insensitive matching
    title_lower = title.lower()

    # If a high-level executive role is found, return the full title
    if any(role.lower() in title_lower for role in executive_roles):
        # Ensure the title does NOT contain excluded words
        if not any(excluded in title_lower for excluded in excluded_roles):
            return title  

    return None  



def process_csv(input_file, output_folder):
    """Process a LinkedIn Sales Navigator CSV file."""
    print(f"Processing: {input_file}")
    
    # Read input CSV file
    df = pd.read_csv(input_file)
    
    # Create standardized column structure
    output_df = pd.DataFrame()
    
    # Process name column
    if 'Name' in df.columns:
        # Split name into first and last name
        try:
            df[['first_name', 'last_name']] = df['Name'].str.split(' ', n=1, expand=True)
        except:
            print("Warning: Could not split Name column properly")
            df['first_name'] = df['Name']
            df['last_name'] = ''
    
    # Map common columns to standardized names
    column_mapping = {
        'Title': 'role',
        'Company': 'company',
        'Location': 'location',
        'Email': 'email',
        'Website': 'website',
        'Profile URL': 'linkedin_url',
        'LinkedIn URL': 'public_linkedin_url'  # Add mapping for the LinkedIn URL column
    }
    
    # Create new dataframe with standardized columns
    for new_col, old_col in column_mapping.items():
        if old_col in df.columns:
            output_df[new_col] = df[old_col]
        else:
            output_df[new_col] = ''
    
    # Add first_name and last_name columns
    if 'first_name' in df.columns:
        output_df['first_name'] = df['first_name']
    if 'last_name' in df.columns:
        output_df['last_name'] = df['last_name']
    
    # Generate output filename
    base_name = os.path.basename(input_file)
    
    # Check if output_folder is a complete path with filename
    if output_folder.endswith('.csv'):
        output_path = output_folder  # Use the exact path provided
    else:
        # Otherwise, use the old behavior of constructing the path
        output_path = os.path.join(output_folder, f"processed_{base_name}")
    
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    print(f"Saved processed file to: {output_path}")
    
    return output_path



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python SalesNav_CSVCleaner.py <input_csv>")
        sys.exit(1)

    input_csv = Path(sys.argv[1]).resolve()
    output_folder = Path(__file__).resolve().parent.parent / "output"

    if not input_csv.exists():
        print(f"Error: File '{input_csv}' not found.")
        sys.exit(1)

    process_csv(input_csv, output_folder)
