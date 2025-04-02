import pandas as pd
import os
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable insecure HTTPS warnings
urllib3.disable_warnings(InsecureRequestWarning)

def process_csv_for_api(filepath):
    """Process CSV file to match API requirements"""
    try:
        df = pd.read_csv(filepath)
        
        # Find phone column - check all variations
        phone_columns = [col for col in df.columns if 'phone' in col.lower() or 'Phone' in col]
        
        if not phone_columns:
            print("No phone columns found!")
            return None
            
        # If we have multiple phone columns, combine them
        if len(phone_columns) > 1:
            # Take first non-empty phone number for each row
            df['Phone'] = df[phone_columns].apply(
                lambda x: next((str(p) for p in x if pd.notna(p) and str(p).strip() != ''), ''),
                axis=1
            )
        else:
            # Rename existing phone column to 'Phone'
            df = df.rename(columns={phone_columns[0]: 'Phone'})
        
        # Clean phone numbers
        df['Phone'] = df['Phone'].astype(str).apply(
            lambda x: ''.join(c for c in x if c.isdigit() or c in ['+', '-', ' '])
        )
        
        # Create processed file
        output_path = filepath.replace('.csv', '_api_ready.csv')
        # Only save the Phone column as that's what the API needs
        df[['Phone']].to_csv(output_path, index=False)
        
        return output_path
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return None

def analyze_csv(filepath):
    """Analyze CSV file structure and content"""
    try:
        print(f"\nAnalyzing file: {filepath}")
        print("-" * 50)
        
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Error: File not found at {filepath}")
            return False
            
        # Read CSV
        df = pd.read_csv(filepath)
        
        # Print basic info
        print("\nFile Structure:")
        print(f"Number of rows: {len(df)}")
        print(f"Number of columns: {len(df.columns)}")
        print("\nColumns found:")
        for col in df.columns:
            print(f"- {col}")
            
        # Find phone columns
        phone_columns = [col for col in df.columns if 'phone' in col.lower() or 'Phone' in col]
        print("\nPhone columns found:")
        for col in phone_columns:
            print(f"- {col}")
            
        if not phone_columns:
            print("\n❌ No phone columns found!")
            return False
            
        # Show sample phone numbers
        print("\nPhone number samples:")
        for col in phone_columns:
            print(f"\n{col}:")
            sample = df[col].head().tolist()
            for phone in sample:
                print(f"- {phone}")
                
        return True
        
    except Exception as e:
        print(f"\nError analyzing file: {str(e)}")
        return False

def test_api_call(filepath):
    """Test API call with the file"""
    if not analyze_csv(filepath):
        print("\nSkipping API test due to format issues")
        return
        
    print("\nProcessing file for API...")
    api_ready_file = process_csv_for_api(filepath)
    
    if not api_ready_file:
        print("Failed to process file for API")
        return
        
    print(f"\nCreated API-ready file: {api_ready_file}")
    print("\nTesting API call...")
    print("-" * 50)
    
    try:
        # API configuration
        url = "https://api.clearoutphone.io/v1/phonenumber/bulk"
        api_token = "a04f0ffd1d4c2a7f2f13447e43e0a640:39ec3ccba26b7756b7099333fde72ff88303adbaa8b8950a482ebcb7091a238c"
        
        # Prepare the request
        with open(api_ready_file, "rb") as file:
            files = {"file": file}
            payload = {"country_code": 'us'}
            headers = {
                'Authorization': f"Bearer:{api_token}",
            }

            # Make the API request
            print("\nMaking test API request...")
            response = requests.request(
                "POST",
                url,
                files=files,
                verify=False,
                headers=headers,
                data=payload
            )

            print("\nAPI Response:")
            print(json.dumps(json.loads(response.text), indent=2))

            if response.status_code == 200:
                print("\n✅ API test successful!")
            else:
                print(f"\n❌ API test failed with status code {response.status_code}")

    except Exception as e:
        print(f"\n❌ Error during API test: {str(e)}")

def main():
    # Test both files
    files = [
        r"C:\Users\siddi\Downloads\leadrocks_automated_list_2025_04_02 (1).csv",
        r"C:\Users\siddi\Downloads\leadrocks_automated_list_2025_04_02_processed.csv"
    ]
    
    for file in files:
        test_api_call(file)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main() 