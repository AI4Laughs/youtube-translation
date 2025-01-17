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
LANGUAGES = ['es', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ko', 'ru']  # List of languages to translate into

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

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"Error refreshing credentials: {e}")
            return None

    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building YouTube service: {e}")
        return None

def translate_text(text, target_language):
    """Translate text using OpenAI's API."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translation assistant."},
                {"role": "user", "content": f"Translate this text to {target_language}: {text}"}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error translating text to {target_language}: {e}")
        return None

def main():
    if not VIDEO_ID:
        print("Error: VIDEO_ID environment variable not set.")
        return

    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate with YouTube API.")
        return

    try:
        # Fetch video details
        print("Fetching video details...")
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
        localizations = video.get('localizations', {})

        # Get original title and description
        original_title = snippet['title']
        original_description = snippet['description']

        # Debug original metadata
        print(f"Original Title: {original_title}")
        print(f"Original Description: {original_description}")

        for lang in LANGUAGES:
            # Translate title and description
            translated_title = translate_text(original_title, lang)
            translated_description = translate_text(original_description, lang)

            if translated_title and translated_description:
                localizations[lang] = {
                    'title': translated_title,
                    'description': translated_description
                }

                # Debug translations
                print(f"Translated Title ({lang}): {translated_title}")
                print(f"Translated Description ({lang}): {translated_description}")

        # Update video with translations
        print("Updating video localizations...")
        update_request = youtube.videos().update(
            part="localizations",
            body={
                "id": VIDEO_ID,
                "localizations": localizations
            }
        )
        update_response = update_request.execute()

        # Debug YouTube API response
        print(f"YouTube API response: {update_response}")
        print("Success! Video metadata translated and updated.")

    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
