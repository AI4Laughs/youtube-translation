import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import openai
from datetime import datetime

# Constants
SCOPES = [
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube'
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

def log_debug(message, data=None):
    """Log debug information with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    if data:
        print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}\n")
    else:
        print()

def get_authenticated_service():
    """Authenticate and return a YouTube service object with detailed logging."""
    creds = None
    log_debug("Starting authentication process")

    try:
        log_debug("Loading oauth2.json")
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            log_debug("OAuth credentials loaded:", {
                "has_token": bool(creds_data.get("token")),
                "has_refresh_token": bool(creds_data.get("refresh_token")),
                "scopes": creds_data.get("scopes")
            })
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        log_debug(f"Error loading credentials: {str(e)}")
        return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log_debug("Refreshing expired credentials")
            try:
                creds.refresh(Request())
                log_debug("Credentials refreshed successfully")
            except Exception as e:
                log_debug(f"Error refreshing credentials: {str(e)}")
                return None
        else:
            log_debug("Invalid credentials state", {
                "exists": bool(creds),
                "valid": bool(creds and creds.valid),
                "has_refresh_token": bool(creds and creds.refresh_token)
            })
            return None

    try:
        log_debug("Building YouTube service")
        service = build('youtube', 'v3', credentials=creds)
        log_debug("YouTube service built successfully")
        return service
    except Exception as e:
        log_debug(f"Error building YouTube service: {str(e)}")
        return None

def test_api_access(youtube):
    """Test API access and permissions."""
    try:
        log_debug(f"Testing API access for video ID: {VIDEO_ID}")
        response = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        ).execute()
        
        if response.get('items'):
            log_debug("Successfully accessed video", {
                "title": response['items'][0]['snippet']['title'],
                "channel": response['items'][0]['snippet']['channelTitle']
            })
            return True
        else:
            log_debug("Video not found or access denied")
            return False
    except Exception as e:
        log_debug(f"API access test failed: {str(e)}")
        return False

def translate_text(text, target_language):
    """Translate text using OpenAI's API with error logging."""
    if not text:
        log_debug(f"Empty text provided for {target_language} translation")
        return None

    try:
        log_debug(f"Translating to {target_language}", {"text_length": len(text)})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {LANGUAGES[target_language]}. Maintain any formatting and special characters."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        translated_text = response['choices'][0]['message']['content'].strip()
        log_debug(f"Translation completed for {target_language}", {
            "original_length": len(text),
            "translated_length": len(translated_text)
        })
        return translated_text
    except Exception as e:
        log_debug(f"Translation error for {target_language}: {str(e)}")
        return None

def main():
    """Main function with comprehensive error checking and logging."""
    log_debug("Starting translation script")
    
    # Environment variable checks
    if not VIDEO_ID:
        log_debug("Error: MY_VIDEO_ID environment variable not set")
        return
    if not OPENAI_API_KEY:
        log_debug("Error: OPENAI_API_KEY environment variable not set")
        return
    
    openai.api_key = OPENAI_API_KEY
    log_debug(f"Processing video ID: {VIDEO_ID}")
    
    # Get YouTube service
    youtube = get_authenticated_service()
    if not youtube:
        log_debug("Failed to create YouTube service")
        return
    
    # Test API access
    if not test_api_access(youtube):
        log_debug("Failed API access test")
        return

    try:
        # Fetch video details
        log_debug("Fetching video details")
        video_response = youtube.videos().list(
            part="snippet,localizations",
            id=VIDEO_ID
        ).execute()

        if not video_response.get("items"):
            log_debug("Video not found or insufficient permissions")
            return

        video = video_response['items'][0]
        snippet = video['snippet']
        original_title = snippet['title']
        original_description = snippet['description']

        log_debug("Video details retrieved", {
            "title": original_title,
            "description_length": len(original_description)
        })

        # Initialize localizations
        if 'localizations' not in video:
            video['localizations'] = {}
        
        updated_localizations = {}

        # Translate to each language
        for lang_code, lang_name in LANGUAGES.items():
            log_debug(f"Processing {lang_name} translation")
            
            translated_title = translate_text(original_title, lang_code)
            translated_description = translate_text(original_description, lang_code)

            if translated_title and translated_description:
                updated_localizations[lang_code] = {
                    'title': translated_title,
                    'description': translated_description
                }
                log_debug(f"Translation completed for {lang_name}")
            else:
                log_debug(f"Failed to translate for {lang_name}")

        if updated_localizations:
            log_debug("Updating video with translations", {
                "languages": list(updated_localizations.keys())
            })
            
            try:
                update_request = youtube.videos().update(
                    part="localizations",
                    body={
                        "id": VIDEO_ID,
                        "localizations": updated_localizations
                    }
                ).execute()

                log_debug("Video update response:", update_request)
                log_debug("Translations successfully updated")
            except HttpError as e:
                error_content = json.loads(e.content)
                log_debug("YouTube API error during update", {
                    "error": error_content.get('error', {}).get('message', str(e)),
                    "status": e.resp.status
                })
        else:
            log_debug("No translations to update")

    except HttpError as e:
        error_content = json.loads(e.content)
        log_debug("YouTube API error", {
            "error": error_content.get('error', {}).get('message', str(e)),
            "status": e.resp.status
        })
    except Exception as e:
        log_debug(f"Unexpected error: {type(e).__name__}", {"error": str(e)})

if __name__ == "__main__":
    main()
