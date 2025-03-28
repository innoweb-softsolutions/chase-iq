"""
Email verification using Hunter.io API
This script checks if emails from LinkedIn leads are valid
"""
import os
import requests
import pandas as pd
import time
import logging

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/email_verifier_{time.strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Hunter.io API details
HUNTER_API_KEY = "e245d54a727765469f2cf49ac56ad9681ce2c1f2"
HUNTER_VERIFY_URL = "https://api.hunter.io/v2/email-verifier"

def verify_email(email):
    """Verify if an email is valid using Hunter.io API"""
    if not email or email.lower() in ['n/a', 'na', '', 'nan', 'none']:
        logger.info(f"Empty email provided, skipping verification")
        return False
    
    logger.info(f"Verifying email: {email}")
    
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
            logger.info(f"Email {email} verification result: status={status}, score={score}")
            
            # Check if email is valid (status is 'deliverable' or score is high)
            is_valid = status == 'deliverable' or score >= 50
            return is_valid
        else:
            logger.warning(f"API error: {response.status_code}, {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying email {email}: {e}")
        return False

def process_csv(file_path):
    """Process a CSV file to verify emails"""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Standardize email column name
        if 'Email' in df.columns and 'email' not in df.columns:
            df['email'] = df['Email']
        elif 'Emails' in df.columns and 'email' not in df.columns:
            df['email'] = df['Emails']
        
        # Ensure 'email' column exists
        if 'email' not in df.columns:
            logger.error(f"CSV is missing required 'Email' column")
            return False
        
        # Clean up email values
        df['email'] = df['email'].astype(str)
        # Remove "+1" or other suffixes from emails
        df['email'] = df['email'].str.replace(r'\+\d+$', '', regex=True)
        # Convert NaN to empty string
        df['email'] = df['email'].replace({'nan': '', 'None': '', 'NaN': '', 'null': ''})
        
        # Initialize counters
        total_leads = len(df)
        verified_count = 0
        invalid_count = 0
        skipped_count = 0
        
        logger.info(f"Found {total_leads} leads in the CSV file")
        
        # Create a new column for verification status
        df['Email_Verified'] = False
        
        # Process each row
        for idx, row in df.iterrows():
            email = str(row['email']).strip()
            
            # Skip empty or N/A emails
            if email.lower() in ['n/a', 'na', '', 'nan', 'none']:
                logger.info(f"Row {idx}: Email is empty or N/A, skipping verification")
                skipped_count += 1
                continue
                
            # Verify the email
            is_valid = verify_email(email)
            
            # Update verification status
            df.at[idx, 'Email_Verified'] = is_valid
            
            if is_valid:
                verified_count += 1
                logger.info(f"Row {idx}: Email {email} is valid")
            else:
                invalid_count += 1
                logger.warning(f"Row {idx}: Email {email} is invalid")
            
            # Add small delay between API calls
            time.sleep(1)
        
        # Save updates back to the CSV file
        df.to_csv(file_path, index=False)
        
        logger.info(f"Processing complete:")
        logger.info(f"  - Total leads: {total_leads}")
        logger.info(f"  - Valid emails: {verified_count}")
        logger.info(f"  - Invalid emails: {invalid_count}")
        logger.info(f"  - Skipped (no email): {skipped_count}")
        logger.info(f"  - Original file updated: {file_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return False

def main():
    """Main function to verify emails in LinkedIn leads CSV files"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Verify emails in LinkedIn leads using Hunter.io API')
    parser.add_argument('--file', help='Specific CSV file to process (relative to output directory)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("LinkedIn Leads Email Verifier")
    print("=" * 60)
    
    if args.file:
        # Process specific file
        # Check if path is absolute or already contains the full path
        if os.path.isabs(args.file) or 'output' in args.file:
            file_path = args.file
        else:
            # Get the current script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # The output directory is one level up and then into output
            output_dir = os.path.join(os.path.dirname(script_dir), "output")
            file_path = os.path.join(output_dir, args.file)
            
        if os.path.exists(file_path):
            process_csv(file_path)
        else:
            logger.error(f"File not found: {file_path}")
    else:
        # Process the most recent CSV file in the output directory
        try:
            # Get the current script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # The output directory is one level up and then into output
            output_dir = os.path.join(os.path.dirname(script_dir), "output")
            
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