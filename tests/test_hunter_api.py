import requests
import json
import os
import glob
import pandas as pd
import time

# Hunter.io API credentials
HUNTER_API_KEY = "e245d54a727765469f2cf49ac56ad9681ce2c1f2"
HUNTER_VERIFY_URL = "https://api.hunter.io/v2/email-verifier"

def get_latest_csv_file(directory=r'E:\Projects\Unfinished\Project Alpha\SalesNav\SalesNav\output'):
    """
    Get the latest CSV file from the specified directory.
    
    Args:
        directory (str): Path to the directory containing CSV files.
        
    Returns:
        str: Path to the latest CSV file.
    """
    list_of_files = glob.glob(os.path.join(directory, '*.csv'))
    if not list_of_files:
        raise FileNotFoundError(f"No CSV files found in the {directory} directory")
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Using latest CSV file: {latest_file}")
    return latest_file

def verify_email(email):
    """
    Verify an email using Hunter.io API
    
    Args:
        email (str): Email to verify
        
    Returns:
        dict: Verification result
    """
    params = {
        'email': email,
        'api_key': HUNTER_API_KEY
    }
    
    try:
        response = requests.get(HUNTER_VERIFY_URL, params=params)
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            print(f"✗ API Error for {email}:", response.status_code)
            print(response.text)
            return None
    except Exception as e:
        print(f"✗ Connection error for {email}: {e}")
        return None

def test_hunter_api():
    print("Testing Hunter.io API integration with minimum usage...")
    
    # Only test with a single well-known email to minimize API usage
    test_email = "ahmadfaisal9900@gmail.com"
    
    params = {
        'email': test_email,
        'api_key': HUNTER_API_KEY
    }
    
    try:
        response = requests.get(HUNTER_VERIFY_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Hunter.io API connection successful!")
            
            # Check email verification status
            status = data['data']['status']
            result = data['data']['result']
            score = data['data'].get('score', 0)
            
            print(f"  Email status: {status}")
            print(f"  Verification result: {result}")
            print(f"  Confidence score: {score}")
            
            if result == "deliverable":
                print(f"✓ Email {test_email} appears to be legitimate")
            else:
                print(f"✗ Email {test_email} may not be legitimate")
                
            print(f"  Used 1 of 50 free verifications")
            return True
        else:
            print("✗ API Error:", response.status_code)
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def test_csv_emails():
    """
    Test emails from the latest CSV file in the output folder.
    """
    try:
        latest_csv = get_latest_csv_file()
        df = pd.read_csv(latest_csv)
        
        # Check if email column exists
        if 'Email' not in df.columns:
            print("✗ No 'email' column found in the CSV file")
            return False
        
        # Filter out empty emails
        emails_to_check = [email for email in df['Email'] if isinstance(email, str) and email.strip()]
        
        if not emails_to_check:
            print("✗ No valid emails found in the CSV file")
            return False
        
        print(f"Found {len(emails_to_check)} emails to check")
        
        # Limit to max 3 emails to reduce API usage
        emails_to_check = emails_to_check[:3]
        
        valid_emails = 0
        for idx, email in enumerate(emails_to_check):
            print(f"\nVerifying email {idx+1}/{len(emails_to_check)}: {email}")
            result = verify_email(email)
            
            if result:
                status = result['status']
                verification = result['result']
                score = result.get('score', 0)
                
                print(f"  Status: {status}")
                print(f"  Result: {verification}")
                print(f"  Score: {score}")
                
                if verification == "deliverable":
                    valid_emails += 1
                    print(f"✓ Email {email} appears to be legitimate")
                else:
                    print(f"✗ Email {email} may not be legitimate")
                
                # Sleep to avoid rate limiting
                if idx < len(emails_to_check) - 1:
                    time.sleep(1)
        
        print(f"\nVerification complete: {valid_emails}/{len(emails_to_check)} emails are valid")
        return valid_emails > 0
    
    except FileNotFoundError as e:
        print(f"✗ {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Error checking emails: {str(e)}")
        return False

if __name__ == "__main__":
    if test_hunter_api():
        print("\nNow checking emails from the latest CSV file...")
        test_csv_emails()
    else:
        print("\nSkipping CSV email verification due to API connection issues")