import os
import sys
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

video_id = "90bad51f-a420-4fc8-8bab-96ea65bfd752"
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

res = sb.table("videos").select("*").eq("id", video_id).single().execute()
video = res.data

title = video.get("target_title", "Documentary Video")[:100]
script_meta = video.get("script_payload", {}).get("meta", {})
description = script_meta.get("description", f"Documentary video: {title}")[:5000]
tags = script_meta.get("tags", ["documentary", "history"])
video_url = video.get("rendered_video_url", "")

print(f"Uploading {video_url} to YouTube...")
print(f"Title: {title}")
print(f"Tags: {tags}")

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
youtube = build('youtube', 'v3', credentials=creds)

body = {
    'snippet': {
        'title': title,
        'description': description,
        'tags': tags,
        'categoryId': '27' # Education
    },
    'status': {
        'privacyStatus': 'private', # Private for now so the user can review it
        'selfDeclaredMadeForKids': False
    }
}

media = MediaFileUpload(video_url, chunksize=-1, resumable=True, mimetype='video/mp4')

request = youtube.videos().insert(
    part=",".join(body.keys()),
    body=body,
    media_body=media
)

response = request.execute()
yt_id = response.get('id')
yt_url = f"https://www.youtube.com/watch?v={yt_id}"

print(f"Uploaded successfully! URL: {yt_url}")

sb.table("videos").update({
    "status": "published",
    "youtube_url": yt_url,
    "youtube_video_id": yt_id,
    "updated_at": datetime.datetime.utcnow().isoformat()
}).eq("id", video_id).execute()

# Notify
sys.path.append("src")
from notifier import notify_published
notify_published(video_id, title, yt_url)
print("Done!")
