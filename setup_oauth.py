import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
import json

# Updated scopes
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube'
]

def main():
    """Generate OAuth credentials with necessary YouTube API scopes."""
    print("Starting OAuth setup...")
    
    # Load client secrets from downloaded file
    if not os.path.exists('client_secrets.json'):
        print("Error: Please download client_secrets.json from Google Cloud Console first!")
        return
        
    # Create flow instance
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json',
        scopes=SCOPES
    )

    # Run local server flow
    creds = flow.run_local_server(port=0)

    # Save credentials
    creds_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }

    # Save to oauth2.json
    with open('oauth2.json', 'w') as f:
        json.dump(creds_data, f)
    
    print("\nSuccessfully created oauth2.json!")
    print("You can now use this file in your GitHub secrets as OAUTH_JSON")

if __name__ == '__main__':
    main()
