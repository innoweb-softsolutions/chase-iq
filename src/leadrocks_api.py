import requests
import os
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable insecure HTTPS warnings
urllib3.disable_warnings(InsecureRequestWarning)

def validate_phone_numbers():
    # API configuration
    url = "https://api.clearoutphone.io/v1/phonenumber/bulk"
    api_token = "a04f0ffd1d4c2a7f2f13447e43e0a640:39ec3ccba26b7756b7099333fde72ff88303adbaa8b8950a482ebcb7091a238c"
    filepath = r"C:\Users\siddi\Downloads\leadrocks_automated_list_2025_04_02_processed.csv"

    # Check if file exists
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return

    try:
        # Prepare the request
        files = {"file": open(filepath, "rb")}
        payload = {"country_code": 'us'}
        headers = {
            'Authorization': f"Bearer:{api_token}",
        }

        # Make the API request
        response = requests.request(
            "POST",
            url,
            files=files,
            verify=False,
            headers=headers,
            data=payload
        )

        # Print the response
        print("API Response:")
        print(response.text)

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
    validate_phone_numbers() 