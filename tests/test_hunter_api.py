import requests
import json

# Hunter.io API credentials
HUNTER_API_KEY = "e245d54a727765469f2cf49ac56ad9681ce2c1f2"
HUNTER_VERIFY_URL = "https://api.hunter.io/v2/email-verifier"

def test_hunter_api():
    print("Testing Hunter.io API integration with minimum usage...")
    
    # Only test with a single well-known email to minimize API usage
    test_email = "info@google.com"
    
    params = {
        'email': test_email,
        'api_key': HUNTER_API_KEY
    }
    
    try:
        response = requests.get(HUNTER_VERIFY_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Hunter.io API connection successful!")
            print(f"  Used 1 of 50 free verifications")
            return True
        else:
            print("✗ API Error:", response.status_code)
            print(response.text)
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

if __name__ == "__main__":
    test_hunter_api()