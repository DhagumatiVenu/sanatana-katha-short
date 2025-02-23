import os
import datetime
import time
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
from google.oauth2.credentials import Credentials
from titles_and_tags import tags_comma_format, tags_hashtag_format, titles
import pytz
import requests
import shutil
import json

# Load YouTube Credentials from GitHub Secrets
CREDENTIALS_FILE = "credentials.json"

try:
    with open(CREDENTIALS_FILE, 'r') as f:
        creds_data = json.load(f)
        print("✅ Credentials Data loaded successfully.")
except FileNotFoundError:
    print(f"❌ Error: {CREDENTIALS_FILE} not found.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"❌ Error: Invalid JSON format in {CREDENTIALS_FILE}. Details: {e}")
    exit(1)

try:
    credentials = Credentials.from_authorized_user_file(CREDENTIALS_FILE)
    print("✅ Credentials loaded successfully.")
except Exception as e:
    print(f"❌ Error loading credentials: {e}")
    exit(1)

# Initialize YouTube API
youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

# Load Telegram Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠ ERROR: Telegram credentials not set. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
    exit(1)

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
        message = f"✅ Added video {title} to playlist 📃 Motivational shorts."
        send_telegram_message(message)
        print(message)
    except Exception as e:
        error_message = f"❌ Error adding video [{title}] to playlist 📃 [Motivational Shorts] Because {e}"
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
        playlist_id="YOUR_PLAYLIST_ID_HERE"  # Replace with your actual playlist ID
    )
    move_video_safely(video_file)

# Optional: Get channel information
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