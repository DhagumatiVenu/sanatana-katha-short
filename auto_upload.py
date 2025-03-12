import os
import datetime
import time
import googleapiclient.discovery
import googleapiclient.errors
import googleapiclient.http
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from titles_and_tags import tags_comma_format, tags_hashtag_format, titles
import pytz
import shutil
import pickle

# YouTube API Configuration
CLIENT_SECRETS_FILE = "client_secrets.json"  # Download this from Google Cloud Console
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.pickle"  # Stores the user's access and refresh tokens

# Folders
uploaded_folder = "uploaded_videos"
os.makedirs(uploaded_folder, exist_ok=True)
video_folder = "upload_videos"
video_files = [f for f in os.listdir(video_folder) if f.endswith(".mp4")]

# Load or refresh YouTube credentials locally
def get_authenticated_service():
    credentials = None
    # Check if token.pickle exists (stored credentials)
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)
    # If no valid credentials, authenticate
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(credentials, token)
    return googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

# Move uploaded videos to archive folder
def move_video_safely(video_file):
    try:
        new_path = os.path.join(uploaded_folder, os.path.basename(video_file))
        shutil.move(video_file, new_path)
        print(f"✅ Moved {video_file} to {uploaded_folder}")
    except Exception as e:
        print(f"❌ Error moving {video_file} to {uploaded_folder} because {e}")

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
        print(f"✅ Added video {title} to playlist 📃Divine Dialogues: Arjuna & Krishna Spiritual Insights Q&A Shorts.")
    except Exception as e:
        print(f"❌ Error adding video [{title}] to playlist because {e}")

# Function to schedule YouTube video upload
def schedule_upload(youtube, video_file, title, description, tags, scheduled_time, playlist_id):
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
        print(f"✅ Scheduled: {title} for {scheduled_time}\n🔗 Video Link: {video_link}")
        
        # Add the video to the specified playlist
        add_to_playlist(youtube, title, video_id, playlist_id)
    except Exception as e:
        print(f"❌ Error uploading {title}. Because {e}")

# Function to get scheduled upload time for a given day offset
def get_scheduled_time(day_offset, hour=8, minute=0):
    timezone = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(timezone)
    scheduled_date = now + datetime.timedelta(days=day_offset)
    scheduled_time = scheduled_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return scheduled_time.isoformat()

# Main logic to schedule 7 videos
if __name__ == "__main__":
    youtube = get_authenticated_service()

    if len(video_files) < 7:
        print(f"⚠ Only {len(video_files)} videos found. Need 7 for a full week.")
        exit(1)

    # Schedule 7 videos for the next 7 days
    playlist_id = "PLiE2xlrohs-hGubskhNMU5rDxjLO9Kydk"  # Replace with your actual playlist ID
    description = "✨ Dive into the profound wisdom of Sanatana Krishna & Arjuna! 🔥 Discover timeless teachings to ignite your inner strength. 💪✨"

    for i in range(1,8):
        video_file = os.path.join(video_folder, video_files[i])
        title_index = int(os.path.splitext(video_files[i])[0])  # Assumes filename is a number matching titles list
        scheduled_time = get_scheduled_time(day_offset=i)  # Schedules for day i (0 = today, 1 = tomorrow, etc.)

        schedule_upload(
            youtube=youtube,
            video_file=video_file,
            title=titles[title_index],
            description=description,
            tags=tags_comma_format,
            scheduled_time=scheduled_time,
            playlist_id=playlist_id
        )
        move_video_safely(video_file)

    print("✅ All 7 videos scheduled successfully!")