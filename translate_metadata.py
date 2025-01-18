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

# Get environment variables with validation
VIDEO_ID = os.getenv('MY_VIDEO_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Print environment variable status (sanitized)
print(f"VIDEO_ID present: {bool(VIDEO_ID)}")
print(f"OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")
print(f"Working with video ID: {VIDEO_ID}")

# Set OpenAI key
openai.api_key = OPENAI_API_KEY

LANGUAGES = {
    'es': 'Spanish',
    'fr': 'French'  # Reduced list for testing
}

def translate_text(text, target_language):
    """Translate text with explicit logging."""
    print(f"\n🔄 Attempting translation to {target_language}")
    print(f"Input text: {text[:100]}...")  # Show first 100 chars
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a translator. Translate to {target_language}."},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        translated = response['choices'][0]['message']['content'].strip()
        print(f"✓ Translation successful. Result: {translated[:100]}...")
        return translated
    except Exception as e:
        print(f"✗ Translation failed: {str(e)}")
        return None

def main():
    print("\n=== Starting YouTube Translation Script ===\n")

    # 1. Validate environment variables
    if not all([VIDEO_ID, OPENAI_API_KEY]):
        print("❌ Missing required environment variables!")
        print(f"VIDEO_ID present: {bool(VIDEO_ID)}")
        print(f"OPENAI_API_KEY present: {bool(OPENAI_API_KEY)}")
        return

    # 2. Test OpenAI API
    print("\n🔍 Testing OpenAI API...")
    try:
        test_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Translate this test to Spanish: Hello"}]
        )
        print("✓ OpenAI API test successful")
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        return

    # 3. Setup YouTube API
    print("\n🔍 Setting up YouTube API...")
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        youtube = build('youtube', 'v3', credentials=creds)
        print("✓ YouTube API setup successful")
    except Exception as e:
        print(f"❌ YouTube API setup failed: {str(e)}")
        return

    # 4. Get video details
    print("\n📺 Fetching video details...")
    try:
        video_response = youtube.videos().list(
            part="snippet,localizations",
            id=VIDEO_ID
        ).execute()

        if not video_response.get('items'):
            print(f"❌ Video not found: {VIDEO_ID}")
            return

        video = video_response['items'][0]
        snippet = video['snippet']
        title = snippet['title']
        description = snippet['description']

        print(f"✓ Found video: {title}")
    except Exception as e:
        print(f"❌ Failed to fetch video: {str(e)}")
        return

    # 5. Perform translations
    print("\n🌍 Starting translations...")
    translations = {}
    
    for lang_code, lang_name in LANGUAGES.items():
        print(f"\nTranslating to {lang_name}...")
        
        # Translate title
        translated_title = translate_text(title, lang_name)
        if not translated_title:
            continue
            
        # Translate description
        translated_description = translate_text(description, lang_name)
        if not translated_description:
            continue

        translations[lang_code] = {
            'title': translated_title,
            'description': translated_description
        }
        print(f"✓ {lang_name} translations completed")

    # 6. Update video
    if translations:
        print("\n📝 Updating video with translations...")
        try:
            update_response = youtube.videos().update(
                part="localizations",
                body={
                    "id": VIDEO_ID,
                    "localizations": translations
                }
            ).execute()
            print("✓ Video updated successfully!")
            print(f"Updated languages: {', '.join(translations.keys())}")
        except Exception as e:
            print(f"❌ Failed to update video: {str(e)}")
    else:
        print("\n❌ No translations to update")

if __name__ == "__main__":
    main()
