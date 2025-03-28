"""
Basic Email Finder for LinkedIn Leads

This script reads LinkedIn leads CSV files, identifies entries with missing emails,
attempts to find them using Snov.io's API, and updates the CSV.
If Snov.io can't find an email or if there are credit issues, it keeps the original value.
"""

import os
import pandas as pd
import requests
import time
from urllib.parse import urlparse
import argparse
import logging

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/email_finder_{time.strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Snov.io API credentials - replace with your actual credentials
SNOV_CLIENT_ID = "c437037b467bc52eafebf948abb4cf82"
SNOV_CLIENT_SECRET = "bc19ba364a6949e08e3192535b456fa6"

# Snov.io API endpoints
SNOV_AUTH_URL = "https://api.snov.io/v1/oauth/access_token"
SNOV_EMAIL_FINDER_URL = "https://api.snov.io/v1/get-emails-from-names"

def get_access_token():
    """Get Snov.io API access token"""
    logger.info("Getting Snov.io API access token...")
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': SNOV_CLIENT_ID,
        'client_secret': SNOV_CLIENT_SECRET
    }
    
    try:
        response = requests.post(SNOV_AUTH_URL, data=payload)
        
        if response.status_code == 200:
            token_data = response.json()
            if 'access_token' in token_data:
                logger.info("Successfully obtained Snov.io access token")
                return token_data['access_token']
        
        logger.warning("Failed to get valid access token")
        return None
    except Exception as e:
        logger.error(f"Error getting access token: {e}")
        return None

def extract_domain(website, company):
    """Extract domain from website URL or company name"""
    # Try website first
    if website and website != "N/A":
        try:
            # Handle URLs without protocol
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            
            parsed_url = urlparse(website)
            domain = parsed_url.netloc or parsed_url.path
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
                
            if domain:
                return domain
        except Exception:
            pass
    
    # Fall back to company name
    if company and company != "N/A":
        company = company.lower()
        for suffix in [' inc', ' llc', ' ltd', ' corp']:
            if company.endswith(suffix):
                company = company[:-len(suffix)]
        
        # Remove non-alphanumeric characters
        company = ''.join(c for c in company if c.isalnum() or c == ' ')
        company = company.strip().replace(' ', '')
        
        if company:
            return f"{company}.com"
    
    return None

def find_email(name, domain, access_token):
    """Find email using Snov.io API, handling errors gracefully"""
    if not name or name == "N/A" or not domain or not access_token:
        return None
    
    # Split name into first and last parts
    name_parts = name.split()
    if len(name_parts) < 2:
        first_name = name_parts[0]
        last_name = ""
    else:
        first_name = name_parts[0]
        last_name = name_parts[-1]
    
    logger.info(f"Searching for email: {first_name} {last_name} at {domain}")
    
    payload = {
        'access_token': access_token,
        'domain': domain,
        'firstName': first_name,
        'lastName': last_name
    }
    
    try:
        response = requests.post(SNOV_EMAIL_FINDER_URL, data=payload)
        
        # If response is OK and has emails
        if response.status_code == 200:
            data = response.json()
            if data.get('emails'):
                emails = data.get('emails', [])
                if emails:
                    # Sort by confidence score (higher is better)
                    emails.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                    best_email = emails[0].get('email')
                    logger.info(f"Found email: {best_email}")
                    return best_email
        
        # If no emails or any error, log and return None
        logger.info(f"No email found or API error for {name} at {domain}")
        return None
        
    except Exception as e:
        logger.warning(f"Error calling Snov.io API: {e}")
        return None

def process_csv(file_path):
    """Process a single CSV file to find missing emails"""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Standardize email column name
        if 'Email' in df.columns and 'email' not in df.columns:
            df['email'] = df['Email']
        elif 'Emails' in df.columns and 'email' not in df.columns:
            df['email'] = df['Emails']
            
        # Standardize name columns
        if 'Name' in df.columns and ('first_name' not in df.columns or 'last_name' not in df.columns):
            # Split Name into first_name and last_name
            try:
                df[['first_name', 'last_name']] = df['Name'].str.split(' ', n=1, expand=True)
            except:
                logger.warning("Could not split Name column into first_name and last_name")
                
        # Standardize company column
        if 'Company' in df.columns and 'company' not in df.columns:
            df['company'] = df['Company']
        
        # Ensure required columns exist
        required_columns = ['email', 'first_name', 'last_name', 'company']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"CSV is missing required columns: {', '.join(missing_columns)}")
            return False
        
        # Clean up values
        for col in df.columns:
            if df[col].dtype != bool:  # Skip boolean columns
                df[col] = df[col].astype(str).replace({'nan': '', 'None': '', 'NaN': '', 'null': ''})
        
        # Get Snov.io API access token
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get Snov.io access token. Exiting.")
            return False
        
        # Initialize counters
        total_leads = len(df)
        missing_email_count = 0
        found_email_count = 0
        
        logger.info(f"Found {total_leads} leads in the CSV file")
        
        # Process each row
        for idx, row in df.iterrows():
            email = str(row['email']).strip()
            
            # Check if email is missing or N/A
            if email.lower() in ['n/a', 'na', '', 'nan', 'none']:
                missing_email_count += 1
                
                first_name = str(row['first_name']).strip()
                last_name = str(row['last_name']).strip()
                company = str(row['company']).strip()
                website = str(row['website']).strip() if 'website' in df.columns else ''
                
                # Extract domain from website or company name
                domain = extract_domain(website, company)
                
                if domain and first_name and last_name:
                    # Try to find email
                    found_email = find_email(f"{first_name} {last_name}", domain, access_token)
                    
                    if found_email:
                        # Update dataframe with found email
                        df.at[idx, 'email'] = found_email
                        found_email_count += 1
                        logger.info(f"Updated email for {first_name} {last_name}: {found_email}")
                    else:
                        logger.info(f"Could not find email for {first_name} {last_name} - keeping original value: {email}")
                else:
                    logger.warning(f"Could not determine domain for {first_name} {last_name} at {company}")
                
            # Add small delay between API calls
            time.sleep(1)
        
        # Save updates back to the original CSV file
        df.to_csv(file_path, index=False)
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Total leads: {total_leads}")
        logger.info(f"  - Leads with missing emails: {missing_email_count}")
        logger.info(f"  - Emails found and updated: {found_email_count}")
        logger.info(f"  - Original file updated: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return False

def main():
    """Main function to process LinkedIn leads CSV files"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Find missing emails for LinkedIn leads using Snov.io API')
    parser.add_argument('--file', help='Specific CSV file to process (relative to output directory)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("LinkedIn Leads Email Finder")
    print("=" * 60)
    
    # Get the current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # The output directory is one level up and then into output
    output_dir = os.path.join(os.path.dirname(script_dir), "output")
    
    if args.file:
        # Process specific file
        file_path = os.path.join(output_dir, args.file)
        if os.path.exists(file_path):
            process_csv(file_path)
        else:
            logger.error(f"File not found: {file_path}")
            logger.info(f"Looking in directory: {output_dir}")
            logger.info(f"Available files: {os.listdir(output_dir) if os.path.exists(output_dir) else 'Directory not found'}")
    else:
        # Process the most recent CSV file in the output directory
        try:
            if not os.path.exists(output_dir):
                logger.error(f"Output directory not found: {output_dir}")
                return
                
            output_files = [f for f in os.listdir(output_dir) if f.endswith(".csv")]
            if not output_files:
                logger.error("No CSV files found in output directory")
                return
            
            # Sort files by modification time (newest first)
            output_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
            latest_file = os.path.join(output_dir, output_files[0])
            
            logger.info(f"Processing most recent file: {latest_file}")
            process_csv(latest_file)
        
        except Exception as e:
            logger.error(f"Error finding CSV files: {e}")

if __name__ == "__main__":
    main()