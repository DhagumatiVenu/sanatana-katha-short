import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# Define YouTube API Scopes
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

# Path to client secrets file (Download this from Google Cloud Console)
CLIENT_SECRETS_FILE = "client_secrets.json"

def authenticate():
    """Runs OAuth flow locally and saves credentials.json"""
    try:
        # Create a flow object using the client secrets file and specified scopes
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)

        # Run the local server flow to get credentials
        credentials = flow.run_local_server(port=8080, prompt="consent", access_type="offline")

        print(f"Authenticated with account: {credentials._client_id}")

        # Save credentials to a JSON file
        credentials_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        with open("credentials.json", "w") as f:
            json.dump(credentials_data, f, indent=4)

        print("✅ credentials.json has been successfully generated!")

    except Exception as e:
        print(f"❌ An error occurred during authentication: {e}")

if __name__ == "__main__":
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"⚠ ERROR: {CLIENT_SECRETS_FILE} is missing. Please download it from Google Cloud Console.")
    else:
        authenticate()