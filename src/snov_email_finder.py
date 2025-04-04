"""
Snov.io Email Finder for Lead Generation

This script processes CSV files containing lead data, finds missing emails
using Snov.io's API, and updates the rows where emails are missing.

It can be used in two ways:
1. As part of the main pipeline (called by main.py)
2. As a standalone tool with command-line arguments

Usage as standalone:
    python snov_email_finder.py --input path/to/input.csv [--output path/to/output.csv]
"""

import os
import pandas as pd
import requests
import time
import logging
import argparse
import dotenv
from urllib.parse import urlparse
from pathlib import Path
import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/snov_email_finder_{time.strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load credentials from .env file
def load_credentials():
    """Load Snov.io API credentials from .env file"""
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # The .env file is always in the config directory
    project_root = os.path.dirname(script_dir)
    if os.path.basename(script_dir) == "src":
        # If we're in the src directory
        env_file = os.path.join(project_root, "config", ".env")
    else:
        # If we're not in the src directory, try going up one level
        env_file = os.path.join(os.path.dirname(project_root), "config", ".env")
    
    if os.path.exists(env_file):
        logger.info(f"Loading credentials from: {env_file}")
        dotenv.load_dotenv(env_file)
    else:
        logger.error(f"Could not find .env file at {env_file}")
    
    # Get credentials from environment variables
    client_id = os.environ.get("SNOV_CLIENT_ID", "")
    client_secret = os.environ.get("SNOV_CLIENT_SECRET", "")
    
    return client_id, client_secret

# Load credentials
SNOV_CLIENT_ID, SNOV_CLIENT_SECRET = load_credentials()

# Snov.io API endpoints
SNOV_AUTH_URL = "https://api.snov.io/v1/oauth/access_token"
SNOV_EMAIL_FINDER_URL = "https://api.snov.io/v1/get-emails-from-names"

def get_access_token():
    """Get Snov.io API access token"""
    logger.info("Getting Snov.io API access token...")
    
    if not SNOV_CLIENT_ID or not SNOV_CLIENT_SECRET:
        logger.error("Snov.io credentials not found. Please set them in your .env file.")
        return None
    
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
        
        logger.warning(f"Failed to get valid access token. Response: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error getting access token: {e}")
        return None

def extract_domain_from_website(website):
    """Extract domain from website URL"""
    if not website or website == "N/A" or pd.isna(website):
        return None
    
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
    except Exception as e:
        logger.warning(f"Could not extract domain from {website}: {e}")
    
    return None

def find_email(first_name, last_name, domain, access_token):
    """Find email using Snov.io API, handling errors gracefully"""
    if not first_name or not last_name or not domain or not access_token:
        return None
    
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
        logger.info(f"No email found or API error for {first_name} {last_name} at {domain}")
        return None
        
    except Exception as e:
        logger.warning(f"Error calling Snov.io API: {e}")
        return None

def get_default_output_path(input_file=None):
    """Get the default output path in the main output folder"""
    # Get the timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create the default output filename
    if input_file:
        input_path = Path(input_file)
        filename = f"{input_path.stem}_snov_{timestamp}.csv"
    else:
        filename = f"snov_processed_{timestamp}.csv"
    
    # Try to find the main output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check possible locations for the output directory
    output_paths = [
        os.path.join(os.path.dirname(script_dir), "output"),  # If in src folder
        os.path.join(script_dir, "output")                   # If in root folder
    ]
    
    for path in output_paths:
        if os.path.exists(path):
            return os.path.join(path, filename)
    
    # If output directory not found, create one in the script directory
    fallback_path = os.path.join(script_dir, "output")
    os.makedirs(fallback_path, exist_ok=True)
    return os.path.join(fallback_path, filename)

def process_csv_file(input_file, output_file=None):
    """Process a CSV file to find missing emails and save to output file
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str, optional): Path to output CSV file. If None, will use the main output folder.
        
    Returns:
        str: Path to the processed output file, or None if processing failed
    """
    logger.info(f"Processing CSV file: {input_file}")
    
    # Generate output filename if not provided
    if output_file is None:
        output_file = get_default_output_path(input_file)
    
    logger.info(f"Output will be saved to: {output_file}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)
        
        # Check if required columns exist
        required_columns = ['first_name', 'last_name', 'email', 'website']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"CSV is missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Get Snov.io API access token
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get Snov.io access token. Exiting.")
            return None
        
        # Initialize counters
        total_leads = len(df)
        missing_email_count = 0
        found_email_count = 0
        
        logger.info(f"Found {total_leads} leads in the CSV data")
        
        # Process each row
        for idx, row in df.iterrows():
            # Convert to string and handle NaN values
            email = str(row['email']).strip() if not pd.isna(row['email']) else ""
            
            # Check if email is missing or N/A
            if email.lower() in ['n/a', 'na', '', 'nan', 'none'] or pd.isna(row['email']):
                missing_email_count += 1
                
                first_name = str(row['first_name']).strip() if not pd.isna(row['first_name']) else ""
                last_name = str(row['last_name']).strip() if not pd.isna(row['last_name']) else ""
                website = str(row['website']).strip() if not pd.isna(row['website']) else ""
                
                # Extract domain from website
                domain = extract_domain_from_website(website)
                
                if domain and first_name and last_name:
                    # Try to find email
                    found_email = find_email(first_name, last_name, domain, access_token)
                    
                    if found_email:
                        # Update dataframe with found email
                        df.at[idx, 'email'] = found_email
                        found_email_count += 1
                        logger.info(f"Updated email for {first_name} {last_name}: {found_email}")
                    else:
                        logger.info(f"Could not find email for {first_name} {last_name} - keeping original value: {email}")
                else:
                    logger.warning(f"Could not determine domain for {first_name} {last_name}")
                
            # Add small delay between API calls
            time.sleep(1)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save the updated dataframe
        df.to_csv(output_file, index=False)
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Total leads: {total_leads}")
        logger.info(f"  - Leads with missing emails: {missing_email_count}")
        logger.info(f"  - Emails found and updated: {found_email_count}")
        logger.info(f"  - Output saved to: {output_file}")
        
        return output_file
    
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return None

def main():
    """Main function with command line argument handling"""
    parser = argparse.ArgumentParser(description='Find missing emails for lead data using Snov.io API')
    parser.add_argument('--input', '-i', help='Input CSV file path')
    parser.add_argument('--output', '-o', help='Output CSV file path (optional)')
    parser.add_argument('--file', help='Alternative input file argument (for compatibility with main.py)')
    args = parser.parse_args()
    
    # Determine which input parameter to use (--input or --file)
    input_file = args.file if args.file else args.input
    
    if not input_file:
        logger.error("No input file specified. Use --input or --file to specify the CSV file.")
        return
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return
    
    # Process the file
    process_csv_file(input_file, args.output)

if __name__ == "__main__":
    main()