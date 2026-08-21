import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
youtube = build('youtube', 'v3', credentials=creds)
request = youtube.channels().list(part="snippet,contentDetails,statistics", mine=True)
response = request.execute()
print(response)
