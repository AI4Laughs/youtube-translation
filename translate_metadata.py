import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import openai

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
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

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

def get_authenticated_service():
    """Authenticate and return a YouTube service object."""
    creds = None

    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        else:
            print("Invalid credentials")
            return None

    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building YouTube service: {e}")
        return None

def translate_text(text, target_language):
    """Translate text using OpenAI's API."""
    if not text:
        print(f"Warning: Empty text provided for translation to {target_language}")
        return None

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a professional translator. Translate the following text to {LANGUAGES[target_language]}. Maintain any formatting, line breaks, and special characters."},
                {"role": "user", "content": text}
            ],
            temperature=0.3  # Lower temperature for more consistent translations
        )
        translated_text = response['choices'][0]['message']['content'].strip()
        if not translated_text:
            print(f"Warning: Empty translation received for language {target_language}")
            return None
        return translated_text
    except Exception as e:
        print(f"Error translating text to {target_language}: {e}")
        return None

def main():
    # Validate environment variables
    if not VIDEO_ID:
        print("Error: MY_VIDEO_ID environment variable not set.")
        return
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate with YouTube API.")
        return

    try:
        # Fetch video details
        print(f"Fetching video details for ID: {VIDEO_ID}")
        video_request = youtube.videos().list(
            part="snippet,localizations",
            id=VIDEO_ID
        )
        video_response = video_request.execute()

        if not video_response.get("items"):
            print("Video not found or insufficient permissions.")
            return

        video = video_response['items'][0]
        snippet = video['snippet']
        
        # Initialize localizations if not present
        if 'localizations' not in video:
            video['localizations'] = {}
        
        localizations = video['localizations']

        # Get original title and description
        original_title = snippet['title']
        original_description = snippet['description']

        print(f"\nOriginal Title: {original_title}")
        print(f"Original Description: {original_description[:100]}...")  # Print first 100 chars

        updated_localizations = {}

        for lang_code, lang_name in LANGUAGES.items():
            print(f"\nTranslating to {lang_name}...")
            
            # Translate title and description
            translated_title = translate_text(original_title, lang_code)
            translated_description = translate_text(original_description, lang_code)

            if translated_title and translated_description:
                updated_localizations[lang_code] = {
                    'title': translated_title,
                    'description': translated_description
                }
                print(f"✓ {lang_name} translation complete")
                print(f"  Title: {translated_title}")
                print(f"  Description: {translated_description[:100]}...")  # Print first 100 chars
            else:
                print(f"✗ Failed to translate to {lang_name}")

        if updated_localizations:
            # Update video with translations
            print("\nUpdating video localizations...")
            update_request = youtube.videos().update(
                part="localizations",
                body={
                    "id": VIDEO_ID,
                    "localizations": updated_localizations
                }
            )
            update_response = update_request.execute()

            if update_response:
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
