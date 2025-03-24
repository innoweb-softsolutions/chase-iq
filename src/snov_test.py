"""
Simple Snov.io Email Finder Test
"""
import requests
import json

# Snov.io API credentials - 
SNOV_CLIENT_ID = "431b2aa328caa43ccb954005edfbb1ee"
SNOV_CLIENT_SECRET = "bfc9449d3ba1c7dc93f2a622a6807c9e"

# Snov.io API endpoint for authentication
SNOV_AUTH_URL = "https://api.snov.io/v1/oauth/access_token"

def get_access_token():
    """Get Snov.io API access token"""
    print("Getting Snov.io API access token...")
    
    payload = {
        'grant_type': 'client_credentials',
        'client_id': SNOV_CLIENT_ID,
        'client_secret': SNOV_CLIENT_SECRET
    }
    
    response = requests.post(SNOV_AUTH_URL, data=payload)
    token_data = response.json()
    
    if 'access_token' in token_data:
        print("✓ Successfully obtained access token")
        return token_data['access_token']
    else:
        print(f"✗ Failed to get access token. Response: {token_data}")
        return None

def get_email_finder():
    token = get_access_token()
    params = {'access_token': token,
              'domain': 'octagon.com',
              'firstName': 'gavin',
              'lastName': 'vanrooyen'
    }

    res = requests.post('https://api.snov.io/v1/get-emails-from-names', data=params)

    return json.loads(res.text)

if __name__ == "__main__":
    print("Testing Snov.io Email Finder API...")
    result = get_email_finder()
    print(json.dumps(result, indent=2))