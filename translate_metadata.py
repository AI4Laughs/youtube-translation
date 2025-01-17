import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import openai

# Constants
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtubepartner'
]
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VIDEO_ID = os.getenv('MY_VIDEO_ID')
LANGUAGES = {
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian'
}

def debug_credentials(creds):
    """Debug credential information."""
    print("\nDebugging Credentials:")
    print(f"Valid: {creds.valid if creds else 'No creds'}")
    print(f"Expired: {creds.expired if creds else 'No creds'}")
    print(f"Has refresh token: {bool(creds.refresh_token) if creds else 'No creds'}")
    print(f"Scopes: {creds.scopes if creds else 'No creds'}\n")

def get_authenticated_service():
    """Authenticate and return a YouTube service object with detailed logging."""
    creds = None
    print("\nStarting authentication process...")

    try:
        print("Attempting to load oauth2.json...")
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            print("oauth2.json loaded successfully")
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            debug_credentials(creds)
    except FileNotFoundError:
        print("Error: oauth2.json file not found")
        return None
    except json.JSONDecodeError:
        print("Error: oauth2.json is not valid JSON")
        return None
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Credentials expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                print("Credentials refreshed successfully")
                debug_credentials(creds)
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        else:
            print("Error: Invalid credentials and unable to refresh")
            return None

    try:
        print("Building YouTube service...")
        service = build('youtube', 'v3', credentials=creds)
        print("YouTube service built successfully")
        return service
    except Exception as e:
        print(f"Error building YouTube service: {e}")
        return None

def test_api_permissions(youtube):
    """Test API permissions and access."""
    try:
        # Test basic video access
        print(f"\nTesting video access for ID: {VIDEO_ID}")
        video_response = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        ).execute()
        
        if video_response.get('items'):
            print("✓ Successfully accessed video information")
        else:
            print("✗ Could not access video information")

        # Test localization permission
        print("\nTesting localization permissions...")
        test_update = youtube.videos().update(
            part="localizations",
            body={
                "id": VIDEO_ID,
                "localizations": {
                    "es": {
                        "title": "Test Title",
                        "description": "Test Description"
                    }
                }
            }
        ).execute()
        print("✓ Successfully tested localization permissions")
        
        return True
    except HttpError as e:
        print(f"Permission test failed: {e.resp.status} {e.content}")
        return False

def main():
    """Main function with enhanced error checking."""
    print("Starting YouTube translation script...")
    
    # Validate environment variables
    if not VIDEO_ID:
        print("Error: MY_VIDEO_ID environment variable not set")
        return
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    print(f"Video ID: {VIDEO_ID}")
    
    # Get YouTube service
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to create YouTube service")
        return
    
    # Test permissions
    if not test_api_permissions(youtube):
        print("Failed permissions test")
        return
    
    print("\nScript completed. Check above for any error messages.")

if __name__ == "__main__":
    main()
