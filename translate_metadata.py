import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import openai

# Updated scopes
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

openai.api_key = OPENAI_API_KEY

def get_authenticated_service():
    """Authenticate and return a YouTube service object."""
    creds = None
    print("\nStarting authentication process...")

    try:
        print("Attempting to load oauth2.json...")
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            print("oauth2.json loaded successfully")
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        else:
            print("Error: Invalid credentials")
            return None

    try:
        print("Building YouTube service...")
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building YouTube service: {e}")
        return None

def translate_text(text, target_language):
    """Translate text using OpenAI's API."""
    if not text:
        return None

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {LANGUAGES[target_language]}. Maintain any formatting and special characters."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error translating to {target_language}: {e}")
        return None

def main():
    if not VIDEO_ID:
        print("Error: MY_VIDEO_ID environment variable not set")
        return
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    print(f"Processing video ID: {VIDEO_ID}")
    
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to create YouTube service")
        return

    try:
        # Fetch video details
        video_response = youtube.videos().list(
            part="snippet,localizations",
            id=VIDEO_ID
        ).execute()

        if not video_response.get("items"):
            print("Video not found or insufficient permissions")
            return

        video = video_response['items'][0]
        snippet = video['snippet']
        original_title = snippet['title']
        original_description = snippet['description']

        print(f"\nOriginal Title: {original_title}")
        print(f"Original Description: {original_description[:100]}...")

        # Initialize localizations if not present
        if 'localizations' not in video:
            video['localizations'] = {}

        updated_localizations = {}

        # Translate to each language
        for lang_code, lang_name in LANGUAGES.items():
            print(f"\nTranslating to {lang_name}...")
            translated_title = translate_text(original_title, lang_code)
            translated_description = translate_text(original_description, lang_code)

            if translated_title and translated_description:
                updated_localizations[lang_code] = {
                    'title': translated_title,
                    'description': translated_description
                }
                print(f"✓ {lang_name} translation complete")
            else:
                print(f"✗ Failed to translate to {lang_name}")

        if updated_localizations:
            print("\nUpdating video with translations...")
            update_request = youtube.videos().update(
                part="localizations",
                body={
                    "id": VIDEO_ID,
                    "localizations": updated_localizations
                }
            ).execute()

            if update_request:
                print("✓ Success! Video metadata translations updated.")
            else:
                print("✗ Failed to update video metadata.")
        else:
            print("\nNo translations to update.")

    except HttpError as e:
        error_content = json.loads(e.content)
        print(f"YouTube API error: {error_content.get('error', {}).get('message', str(e))}")
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
