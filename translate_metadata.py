import os
import openai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
VIDEO_ID = os.getenv('MY_VIDEO_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Store your OpenAI API key in GitHub Secrets or locally

# Target languages and their names for translation
TARGET_LANGUAGES = {
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Simplified Chinese',
    'hi': 'Hindi'
}

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

def get_authenticated_service():
    """Authenticate with the YouTube API."""
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

def translate_with_openai(text, target_language_name):
    """Translate text using OpenAI."""
    try:
        prompt = f"Translate the following text to {target_language_name}:\n\n{text}"
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=500
        )
        translation = response.choices[0].text.strip()
        return translation
    except Exception as e:
        print(f"Error translating text with OpenAI: {e}")
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

            for lang_code, lang_name in TARGET_LANGUAGES.items():
                translated_title = translate_with_openai(original_title, lang_name)
                translated_description = translate_with_openai(original_description, lang_name)

                # Update the metadata
                update_video_metadata(youtube, video_id, translated_title, translated_description, lang_code)

    except HttpError as e:
        print(f"An HTTP error occurred: {e.resp.status} {e.content}")
    except Exception as e:
        print(f"An unexpected error occurred: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
