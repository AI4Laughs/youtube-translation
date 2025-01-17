import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import translate_v2 as translate

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_KEY = os.getenv('GOOGLE_TRANSLATE_API_KEY')  # Your Translate API key
TARGET_LANGUAGES = ['es', 'fr', 'de', 'zh', 'hi']  # List of languages to translate to

def get_authenticated_service():
    """Authenticate with YouTube API."""
    creds = None
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    if not creds or not creds.valid:
        print("Invalid credentials. Please ensure oauth2.json is properly configured.")
        return None

    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building service: {e}")
        return None

def translate_text(text, target_language, translate_client):
    """Translate text using Google Translate API."""
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        print(f"Error translating text: {e}")
        return text

def update_video_metadata(youtube, video_id, title, description, language):
    """Update video metadata for a specific language."""
    try:
        response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        if not response.get("items"):
            print("Video not found or insufficient permissions.")
            return

        current_snippet = response['items'][0]['snippet']
        current_snippet['title'] = title
        current_snippet['description'] = description
        current_snippet['defaultLanguage'] = language
        current_snippet['localized'] = {'title': title, 'description': description}

        youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": current_snippet
            }
        ).execute()
        print(f"Updated metadata for video ID {video_id} to language {language}.")
    except HttpError as e:
        print(f"HTTP error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    print("Authenticating YouTube API...")
    youtube = get_authenticated_service()
    if not youtube:
        return

    translate_client = translate.Client(api_key=API_KEY)

    print("Fetching videos from your channel...")
    try:
        video_request = youtube.search().list(
            part="id",
            forMine=True,
            type="video",
            maxResults=50
        )
        video_response = video_request.execute()

        for item in video_response.get("items", []):
            video_id = item["id"]["videoId"]
            print(f"Processing video ID: {video_id}")

            # Fetch video metadata
            video_details = youtube.videos().list(
                part="snippet",
                id=video_id
            ).execute()

            snippet = video_details['items'][0]['snippet']
            original_title = snippet['title']
            original_description = snippet.get('description', '')

            for lang in TARGET_LANGUAGES:
                translated_title = translate_text(original_title, lang, translate_client)
                translated_description = translate_text(original_description, lang, translate_client)

                # Update the metadata
                update_video_metadata(youtube, video_id, translated_title, translated_description, lang)

    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
