import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import openai
from datetime import datetime

def test_openai_api():
    """Test OpenAI API access."""
    print("\nTesting OpenAI API access...")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator."},
                {"role": "user", "content": "Translate this test message to Spanish: Hello world"}
            ],
            temperature=0.3
        )
        translated = response['choices'][0]['message']['content'].strip()
        print(f"✓ OpenAI API test successful. Test translation: {translated}")
        return True
    except Exception as e:
        print(f"✗ OpenAI API test failed: {str(e)}")
        return False

def test_youtube_api(youtube, video_id):
    """Test YouTube API access and permissions."""
    print("\nTesting YouTube API access...")
    try:
        video_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()
        
        if video_response.get('items'):
            video = video_response['items'][0]
            print(f"✓ YouTube API test successful")
            print(f"  Video title: {video['snippet']['title']}")
            print(f"  Channel: {video['snippet']['channelTitle']}")
            return True
        else:
            print("✗ Video not found or access denied")
            return False
    except Exception as e:
        print(f"✗ YouTube API test failed: {str(e)}")
        return False

def test_youtube_update(youtube, video_id):
    """Test YouTube API update permissions."""
    print("\nTesting YouTube API update permissions...")
    try:
        # Try to update with current title (no actual change)
        video_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()
        
        if not video_response.get('items'):
            print("✗ Cannot fetch video details")
            return False
            
        current_title = video_response['items'][0]['snippet']['title']
        
        update_response = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": current_title,
                    "categoryId": video_response['items'][0]['snippet']['categoryId']
                }
            }
        ).execute()
        
        print("✓ YouTube API update test successful")
        return True
    except Exception as e:
        print(f"✗ YouTube API update test failed: {str(e)}")
        return False

def main():
    """Main function with API tests."""
    print("Starting translation script with API tests...")
    
    # Check environment variables
    VIDEO_ID = os.getenv('MY_VIDEO_ID')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not VIDEO_ID:
        print("Error: MY_VIDEO_ID environment variable not set")
        return
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
        
    print(f"Video ID: {VIDEO_ID}")
    
    # Test OpenAI API
    openai.api_key = OPENAI_API_KEY
    if not test_openai_api():
        print("OpenAI API test failed. Stopping script.")
        return
    
    # Get YouTube service
    try:
        print("\nLoading YouTube credentials...")
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, [
                'https://www.googleapis.com/auth/youtube.force-ssl',
                'https://www.googleapis.com/auth/youtube'
            ])
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                print("Invalid credentials")
                return
                
        youtube = build('youtube', 'v3', credentials=creds)
        print("YouTube service created successfully")
        
    except Exception as e:
        print(f"Error setting up YouTube service: {str(e)}")
        return
    
    # Test YouTube API access
    if not test_youtube_api(youtube, VIDEO_ID):
        print("YouTube API access test failed. Stopping script.")
        return
        
    # Test YouTube update permissions
    if not test_youtube_update(youtube, VIDEO_ID):
        print("YouTube API update test failed. Stopping script.")
        return
        
    print("\nAll API tests passed successfully!")
    print("If you're seeing this message but translations aren't working,")
    print("please share the full logs so we can investigate further.")

if __name__ == "__main__":
    main()
