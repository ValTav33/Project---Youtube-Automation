import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"

# Expanded Scopes for Phase 7: Analytics Ingestion + Video Uploads
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]

def get_authenticated_service(api_service_name: str, api_version: str):
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}. Re-authenticating...")
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(f"Missing {CLIENT_SECRETS_FILE}. Please create OAuth credentials in Google Cloud Console.")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build(api_service_name, api_version, credentials=creds)
