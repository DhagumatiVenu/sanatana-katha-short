import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Load YouTube Credentials
CREDENTIALS_FILE = "credentials.json"
CLIENT_SECRETS_FILE = "client_secrets.json"  # Contains your OAuth client ID and secret
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]

def reauthorize_app():
    """Reauthorize the app and generate a new credentials.json file."""
    print("Starting reauthorization flow...")
    try:
        # Start the OAuth 2.0 flow
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)  # Opens a browser for authorization

        # Save the new credentials to credentials.json
        with open(CREDENTIALS_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        print("✅ New credentials saved to credentials.json.")
    except Exception as e:
        print(f"❌ Error during reauthorization: {e}")

# Call this function if credentials are invalid or revoked
with open(CREDENTIALS_FILE, "w") as token_file:
    print(token_file.readlines)
reauthorize_app()