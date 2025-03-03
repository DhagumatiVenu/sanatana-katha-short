import os
import datetime
import time
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from titles_and_tags import tags_comma_format, tags_hashtag_format, titles
import pytz
import requests
import shutil
import json

# Load YouTube Credentials
CREDENTIALS_FILE = "credentials.json"
CLIENT_SECRETS_FILE = "client_secrets.json"  # Not used in GitHub Actions
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ensure uploaded_videos folder exists
uploaded_folder = "uploaded_videos"
os.makedirs(uploaded_folder, exist_ok=True)

# Folder for the videos to upload
video_folder = "upload_videos"
video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]
video_file = os.path.join(video_folder, video_files[0])

# Function to send Telegram notifications
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"⚠ Telegram Error: {e}")

def refresh_access_token(refresh_token, client_id, client_secret):
    """Refresh the access token using the refresh token."""
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        print("Sending refresh token request...")
        send_telegram_message("Sending refresh token request...")
        response = requests.post(token_url, data=payload)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error refreshing access token: {e}")
        send_telegram_message(f"❌ Error refreshing access token: {e}")
        return None

def load_or_refresh_credentials():
    """Load credentials or refresh them if expired."""
    creds = None

    # Check if credentials file exists
    if os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
            print("✅ Credentials loaded successfully.")
            send_telegram_message("✅ Credentials loaded successfully.")
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            send_telegram_message(f"❌ Error loading credentials: {e}")
            creds = None

    # If no valid credentials, refresh or notify about revocation
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            send_telegram_message("Refreshing expired credentials...")
            new_access_token = refresh_access_token(
                creds.refresh_token,
                creds.client_id,
                creds.client_secret,
            )
            if new_access_token:
                creds.token = new_access_token
                creds.expiry = None  # Reset expiry to allow the library to calculate it
                print("✅ Credentials refreshed successfully.")
                send_telegram_message("✅ Credentials refreshed successfully.")
            else:
                print("❌ Failed to refresh credentials.")
                send_telegram_message("❌ Failed to refresh credentials.")
                creds = None
        else:
            # Notify via Telegram if credentials are revoked or missing
            error_message = (
                "❌ Credentials missing or revoked. Please reauthorize the app:\n"
                "1. Run the script locally.\n"
                "2. Follow the authorization steps to generate a new credentials.json file.\n"
                "3. Update the GitHub Secret with the new credentials."
            )
            send_telegram_message(error_message)
            print(error_message)
            exit(1)

        # Save the updated credentials to the file
        if creds:
            with open(CREDENTIALS_FILE, "w") as token_file:
                token_file.write(creds.to_json())
                print("✅ Updated credentials saved to credentials.json.")

    return creds

# Load or refresh credentials
credentials = load_or_refresh_credentials()

# Initialize YouTube API
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠ ERROR: Telegram credentials not set. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    

# Move uploaded videos to archive folder
def move_video_safely(video_file):
    try:
        new_path = os.path.join(uploaded_folder, os.path.basename(video_file))
        shutil.move(video_file, new_path)
        message = f"✅ Moved {video_file} to {uploaded_folder}"
        send_telegram_message(message)
        print(message)
    except Exception as e:
        error_message = f"❌ Error moving {video_file} to {uploaded_folder} because {e}"
        send_telegram_message(error_message)
        print(error_message)

# Function to add a video to a playlist
def add_to_playlist(youtube, title, video_id, playlist_id):
    try:
        request_body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        request = youtube.playlistItems().insert(part="snippet", body=request_body)
        response = request.execute()
        message = f"✅ Added video {title} to playlist 📃Divine Dialogues: Arjuna & Krishna Spiritual Insights Q&A Shorts."
        send_telegram_message(message)
        print(message)
    except Exception as e:
        error_message = f"❌ Error adding video [{title}] to playlist 📃Divine Dialogues: Arjuna & Krishna Spiritual Insights Q&A Shorts. Because {e}"
        send_telegram_message(error_message)
        print(error_message)

# Function to schedule YouTube video upload
def schedule_upload(video_file, title, description, tags, scheduled_time, playlist_id):
    try:
        request_body = {
            "snippet": {
                "title": title,
                "description": description + " " + tags_hashtag_format,
                "tags": tags,
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": scheduled_time
            }
        }
        media = googleapiclient.http.MediaFileUpload(video_file, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)
        response = request.execute()
        video_id = response['id']
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        message = f"✅ Scheduled: {title} for {scheduled_time}\n🔗 Video Link: {video_link}"
        send_telegram_message(message)
        print(message)
        
        # Add the video to the specified playlist
        add_to_playlist(youtube, title, video_id, playlist_id)
    except Exception as e:
        error_message = f"❌ Error uploading {title}. Because {e}"
        send_telegram_message(error_message)
        print(error_message)
        exit(1)

# Function to get the scheduled upload time
def get_scheduled_time(hour, minute):
    timezone = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(timezone)
    scheduled_date = now + datetime.timedelta(days=1)
    scheduled_time = scheduled_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return scheduled_time.isoformat()

# Upload the first video in the list
if len(video_files) >= 1:
    schedule_upload(
        video_file=video_file, 
        title=titles[int(os.path.splitext(video_files[0])[0])],
        description="✨ Dive into the profound wisdom of Sanatana Krishna & Arjuna! 🔥 Discover timeless teachings to ignite your inner strength. 💪✨", 
        tags=tags_comma_format,  # Modify tags as needed
        scheduled_time=get_scheduled_time(8, 0),
        playlist_id="PLiE2xlrohs-hGubskhNMU5rDxjLO9Kydk"  # Replace with your actual playlist ID
    )
    move_video_safely(video_file)

# Optional: Get channel informations
# def get_channel_info():
#     try:
#         response = youtube.channels().list(
#             part="snippet",
#             mine=True
#         ).execute()
#         if 'items' in response and len(response['items']) > 0:
#             channel = response['items'][0]
#             print(f"Channel Title: {channel['snippet']['title']}")
#             print(f"Channel ID: {channel['id']}")
#         else:
#             print("No channels found.")
#     except Exception as e:
#         print(f"Error getting channel info: {e}")