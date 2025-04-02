import requests
import os
from urllib3.exceptions import InsecureRequestWarning
import urllib3
import json
from datetime import datetime

# Disable insecure HTTPS warnings
urllib3.disable_warnings(InsecureRequestWarning)

def validate_phone_numbers(filepath=None):
    # API configuration
    url = "https://api.clearoutphone.io/v1/phonenumber/bulk"
    api_token = "a04f0ffd1d4c2a7f2f13447e43e0a640:39ec3ccba26b7756b7099333fde72ff88303adbaa8b8950a482ebcb7091a238c"
    
    # Use provided filepath or default to the one in output directory
    if not filepath:
        filepath = r"C:\Users\siddi\Desktop\chase-iq\output\run_20250403_002034\processed\leadrocks_automated_list_2025_04_02_processed.csv"

    # Check if file exists
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return

    try:
        print(f"Processing file: {filepath}")
        
        # Prepare the request
        files = {"file": open(filepath, "rb")}
        payload = {"country_code": 'us'}
        headers = {
            'Authorization': f"Bearer:{api_token}",
        }

        # Make the API request
        print("Making API request...")
        response = requests.request(
            "POST",
            url,
            files=files,
            verify=False,
            headers=headers,
            data=payload
        )

        # Save response to a JSON file in the same directory
        response_file = filepath.replace('.csv', '_api_response.json')
        with open(response_file, 'w') as f:
            json.dump(json.loads(response.text), f, indent=2)
        
        print(f"\nAPI Response saved to: {response_file}")
        print("\nAPI Response:")
        print(json.dumps(json.loads(response.text), indent=2))

        # Check if the request was successful
        if response.status_code == 200:
            print("\nPhone number validation completed successfully!")
        else:
            print(f"\nError: API request failed with status code {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Ensure the file is closed
        if 'files' in locals() and files.get('file'):
            files['file'].close()

if __name__ == "__main__":
    # You can provide a different filepath as an argument if needed
    validate_phone_numbers() 