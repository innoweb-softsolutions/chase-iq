import os
import sys
import pandas as pd
import re
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

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
    """Process the CSV file and save the output."""
    df = pd.read_csv(input_file)

    # Clean names
    df[['first_name', 'last_name']] = df['Name'].astype(str).apply(clean_name).apply(pd.Series)
    df = df.dropna(subset=['first_name', 'last_name'])

    # Extract roles
    df['Role'] = df['Title'].astype(str).apply(extract_role)
    df = df.dropna(subset=['Role'])

    # Ensure business emails are used, but keep personal emails if a domain exists
    df['Emails'] = df['Email'].apply(lambda x: x if is_business_email(str(x)) else "N/A")

    # Extract domain from website or company name
    df['Domain'] = df.apply(lambda row: extract_domain(str(row['Website']), str(row['Company'])), axis=1)

    # Drop rows where both email is personal AND no domain exists
    df = df[~((df['Emails'] == "N/A") & (df['Domain'].isna()))]

    
    df['Phone'] = 'N/A'

    
    df['Misc'] = df['Profile URL']

  
    df = df[['first_name', 'last_name', 'Role', 'Emails', 'Domain', 'Phone', 'Misc']]

    print(f"Final Row Count: {len(df)}") 

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Save processed file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_folder / f'processed_leads_{timestamp}.csv'

    df.to_csv(output_file, index=False)
    print(f"Processed file saved: {output_file}")



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
