import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import openai
import json

# Constants
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
VIDEO_ID = os.getenv("MY_VIDEO_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Languages for translation
TARGET_LANGUAGES = ["es", "fr", "de", "it", "pt", "ja", "ko"]

def get_authenticated_service():
    """Authenticate and return a YouTube API service object."""
    creds = None
    if os.path.exists("oauth2.json"):
        with open("oauth2.json", "r") as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Invalid credentials. Please ensure oauth2.json is properly configured.")
            return None

    return build("youtube", "v3", credentials=creds)

def translate_text(text, target_language):
    """Translate text using OpenAI API."""
    openai.api_key = OPENAI_API_KEY
    prompt = f"Translate the following text to {target_language}:\n\n{text}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
    )
    return response.choices[0].text.strip()

def main():
    if not VIDEO_ID:
        print("Error: VIDEO_ID environment variable not set")
        return

    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate with YouTube API")
        return

    try:
        # Fetch the video details
        video_request = youtube.videos().list(
            part="snippet,localizations",
            id=VIDEO_ID
        )
        video_response = video_request.execute()

        if not video_response["items"]:
            print("Video not found or insufficient permissions.")
            return

        video = video_response["items"][0]
        snippet = video["snippet"]
        title = snippet["title"]
        description = snippet["description"]
        localizations = video.get("localizations", {})

        # Translate title and description into target languages
        for lang in TARGET_LANGUAGES:
            translated_title = translate_text(title, lang)
            translated_description = translate_text(description, lang)
            localizations[lang] = {
                "title": translated_title,
                "description": translated_description,
            }
            print(f"Translated into {lang}: {translated_title}")

        # Update the video with translations
        update_request = youtube.videos().update(
            part="localizations",
            body={
                "id": VIDEO_ID,
                "localizations": localizations
            }
        )
        update_request.execute()
        print("Successfully updated video with translations.")

    except Exception as e:
        print(f"An error occurred: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
