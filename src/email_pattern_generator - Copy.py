"""
Email pattern generation fallback for LinkedIn leads
This script implements fallback pattern generation when Snov.io can't find emails
"""
import os
import requests
import pandas as pd
import time
import logging
import re

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/pattern_generator_{time.strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Hunter.io API details
HUNTER_API_KEY = "e245d54a727765469f2cf49ac56ad9681ce2c1f2"
HUNTER_VERIFY_URL = "https://api.hunter.io/v2/email-verifier"

def extract_domain_from_website(website):
    """Extract domain from website URL"""
    if website and website.lower() != 'n/a':
        # Handle URLs without protocol
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            # Extract domain using regex
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', website)
            if domain_match:
                return domain_match.group(1)
        except Exception as e:
            logger.warning(f"Error extracting domain from website: {e}")
    
    return None

def extract_domain_from_company(company):
    """Extract domain from company name"""
    if company and company.lower() != 'n/a':
        # Clean up company name
        company = company.lower()
        company = re.sub(r'\s+(inc|llc|ltd|corp|co)\.?$', '', company)
        company = re.sub(r'[^\w\s]', '', company)
        company = company.strip().replace(' ', '')
        
        if company:
            return f"{company}.com"
    
    return None

def generate_email_patterns(first_name, last_name, domain):
    """Generate various email patterns based on name and domain"""
    if not first_name or not last_name or not domain:
        return []
    
    # Clean up names
    first_name = first_name.lower().strip()
    last_name = last_name.lower().strip()
    
    # Generate common patterns
    patterns = [
        f"{first_name}@{domain}",
        f"{last_name}@{domain}",
        f"{first_name}{last_name}@{domain}",
        f"{first_name}.{last_name}@{domain}",
        f"{first_name[0]}{last_name}@{domain}",
        f"{first_name[0]}.{last_name}@{domain}",
        f"{first_name}_{last_name}@{domain}",
        f"{first_name}-{last_name}@{domain}",
        f"{last_name}{first_name}@{domain}",
        f"{last_name}.{first_name}@{domain}",
        # Try with first name shortened (e.g., Dave for David)
        f"{first_name[:3]}@{domain}" if len(first_name) > 3 else None,
        f"{first_name[:3]}{last_name}@{domain}" if len(first_name) > 3 else None
    ]
    
    # Remove any None entries
    return [p for p in patterns if p]

def verify_email(email):
    """Verify if an email is valid using Hunter.io API"""
    if not email or email.lower() in ['n/a', 'na', '', 'nan', 'none']:
        return False
    
    logger.info(f"Verifying email pattern: {email}")
    
    params = {
        'email': email,
        'api_key': HUNTER_API_KEY
    }
    
    try:
        response = requests.get(HUNTER_VERIFY_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract verification result
            result = data.get('data', {})
            
            # Log detailed verification info
            status = result.get('status', '')
            score = result.get('score', 0)
            logger.info(f"Pattern {email} verification: status={status}, score={score}")
            
            # Check if email is valid
            is_valid = status == 'deliverable' or score >= 50
            return is_valid
        else:
            logger.warning(f"API error: {response.status_code}, {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying email pattern {email}: {e}")
        return False

def process_csv(file_path):
    """Process a CSV file to generate email patterns for missing emails"""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Ensure required columns exist
        if 'Email' not in df.columns:
            logger.error(f"CSV is missing required 'Email' column")
            return False
        
        # Initialize counters
        total_leads = len(df)
        missing_email_count = 0
        patterns_generated = 0
        patterns_verified = 0
        
        logger.info(f"Found {total_leads} leads in the CSV file")
        
        # Add pattern generation tracking column
        df['Email_Pattern_Generated'] = False
        
        # Process each row
        for idx, row in df.iterrows():
            email = str(row['Email']).strip() if pd.notna(row['Email']) else ""
            
            # Only process rows with missing or N/A emails
            if email.lower() in ['n/a', 'na', '', 'nan', 'none']:
                missing_email_count += 1
                logger.info(f"Row {idx}: Email is missing, attempting pattern generation")
                
                # Parse name into first and last name
                name = row.get('Name', '')
                if name:
                    name_parts = name.split()
                    first_name = name_parts[0] if name_parts else ""
                    last_name = name_parts[-1] if len(name_parts) > 1 else ""
                else:
                    first_name = ""
                    last_name = ""
                
                # Get domain from website or company name
                domain = None
                website = row.get('Website', '')
                if website:
                    domain = extract_domain_from_website(website)
                
                if not domain:
                    company = row.get('Company', '')
                    if company:
                        domain = extract_domain_from_company(company)
                
                # Generate and verify email patterns
                if first_name and last_name and domain:
                    patterns_generated += 1
                    logger.info(f"Generating email patterns for {first_name} {last_name} at {domain}")
                    email_patterns = generate_email_patterns(first_name, last_name, domain)
                    
                    valid_emails = []
                    for pattern in email_patterns:
                        if verify_email(pattern):
                            valid_emails.append(pattern)
                            # Break after finding the first valid pattern to save API calls
                            break
                    
                    if valid_emails:
                        patterns_verified += 1
                        best_email = valid_emails[0]  # Use the first valid email pattern
                        df.at[idx, 'Email'] = best_email
                        df.at[idx, 'Email_Pattern_Generated'] = True
                        logger.info(f"Found valid email pattern: {best_email}")
                    else:
                        logger.warning(f"No valid email patterns found for {first_name} {last_name} at {domain}")
                else:
                    logger.warning(f"Insufficient data to generate email patterns for row {idx}")
            
            # Add small delay between API calls
            time.sleep(1)
        
        # Save updates back to the CSV file
        df.to_csv(file_path, index=False)
        
        logger.info(f"Pattern generation complete:")
        logger.info(f"  - Total leads: {total_leads}")
        logger.info(f"  - Leads with missing emails: {missing_email_count}")
        logger.info(f"  - Patterns generated: {patterns_generated}")
        logger.info(f"  - Leads with verified pattern emails: {patterns_verified}")
        logger.info(f"  - Original file updated: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return False

def main():
    """Main function to generate email patterns for LinkedIn leads with missing emails"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate email patterns for LinkedIn leads with missing emails')
    parser.add_argument('--file', help='Specific CSV file to process (relative to output directory)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("LinkedIn Leads Email Pattern Generator")
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