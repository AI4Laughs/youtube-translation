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
    print(f"\n[{timestamp}] {message}")
    if data:
        try:
            print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            print(f"Data: {str(data)}")

def test_apis():
    """Test both OpenAI and YouTube APIs."""
    log_debug("Testing OpenAI API...")
    try:
        openai.api_key = OPENAI_API_KEY
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator."},
                {"role": "user", "content": "Test message: Hello"}
            ]
        )
        log_debug("OpenAI API test successful", {
            "response": response['choices'][0]['message']['content']
        })
    except Exception as e:
        log_debug("OpenAI API test failed", {"error": str(e)})
        return False
    return True

def get_authenticated_service():
    """Get authenticated YouTube service with detailed logging."""
    log_debug("Starting YouTube authentication")
    
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            log_debug("OAuth credentials loaded", {
                "has_token": bool(creds_data.get("token")),
                "has_refresh_token": bool(creds_data.get("refresh_token")),
                "scopes": creds_data.get("scopes")
            })
    except Exception as e:
        log_debug("Failed to load oauth2.json", {"error": str(e)})
        return None

    try:
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                log_debug("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                log_debug("Invalid credentials state")
                return None
        
        youtube = build('youtube', 'v3', credentials=creds)
        log_debug("YouTube service built successfully")
        
        # Test the service
        test_response = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        ).execute()
        
        if test_response.get('items'):
            log_debug("YouTube API test successful", {
                "video_title": test_response['items'][0]['snippet']['title']
            })
        else:
            log_debug("YouTube API test failed - No video found")
            return None
            
        return youtube
    except Exception as e:
        log_debug("Error in YouTube authentication", {"error": str(e)})
        return None

def translate_and_update():
    """Main translation and update logic with detailed logging."""
    if not all([VIDEO_ID, OPENAI_API_KEY]):
        log_debug("Missing required environment variables", {
            "has_video_id": bool(VIDEO_ID),
            "has_openai_key": bool(OPENAI_API_KEY)
        })
        return

    log_debug("Starting translation process", {"video_id": VIDEO_ID})

    # Test APIs first
    if not test_apis():
        log_debug("API tests failed")
        return

    youtube = get_authenticated_service()
    if not youtube:
        log_debug("Failed to get YouTube service")
        return

    try:
        # Get video details
        video_response = youtube.videos().list(
            part="snippet,localizations",
            id=VIDEO_ID
        ).execute()

        if not video_response.get('items'):
            log_debug("Video not found")
            return

        video = video_response['items'][0]
        snippet = video['snippet']
        log_debug("Retrieved video details", {
            "title": snippet['title'],
            "description_length": len(snippet['description'])
        })

        # Perform translations
        translations = {}
        for lang_code, lang_name in LANGUAGES.items():
            log_debug(f"Translating to {lang_name}")
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"Translate to {lang_name}:"},
                        {"role": "user", "content": snippet['title']}
                    ]
                )
                translated_title = response['choices'][0]['message']['content']
                
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"Translate to {lang_name}:"},
                        {"role": "user", "content": snippet['description']}
                    ]
                )
                translated_desc = response['choices'][0]['message']['content']
                
                translations[lang_code] = {
                    'title': translated_title,
                    'description': translated_desc
                }
                log_debug(f"Translation completed for {lang_name}", {
                    "title": translated_title[:50] + "..."
                })
            except Exception as e:
                log_debug(f"Translation failed for {lang_name}", {"error": str(e)})

        # Update video with translations
        if translations:
            log_debug("Updating video with translations", {
                "languages": list(translations.keys())
            })
            try:
                update_response = youtube.videos().update(
                    part="localizations",
                    body={
                        "id": VIDEO_ID,
                        "localizations": translations
                    }
                ).execute()
                log_debug("Update successful", {"response": update_response})
            except Exception as e:
                log_debug("Update failed", {"error": str(e)})
        else:
            log_debug("No translations to update")

    except Exception as e:
        log_debug("Process failed", {"error": str(e)})

if __name__ == "__main__":
    translate_and_update()
