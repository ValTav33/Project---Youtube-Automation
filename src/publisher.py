#!/usr/bin/env python3
"""
Publishing & Feedback Loop Engine
- Publishes videos to YouTube channel via YouTube Data API v3 or n8n webhook
- Uses centralized notifier.py for all Telegram notifications
- Reads exactly from the strictly versioned PublishPackage artifact.
"""

import os
import sys
import datetime
import logging
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv
from supabase import create_client
from notifier import notify_step_failed, notify_published

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

def get_supabase():
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def send_telegram_review_gate(video_id: str):
    """
    Dispatches a Telegram review card with preview link, thumbnails, and 1-click publish button.
    Now reads directly from PublishPackage artifact.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram bot credentials not configured. Skipping review gate.")
        return

    sb = get_supabase()
    
    # Get Video context
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data
    if not video:
        logger.error(f"Video {video_id} not found.")
        return

    # Get PublishPackage
    art_res = sb.table("artifacts").select("*").eq("video_id", video_id).eq("artifact_type", "PublishPackage").order("revision", desc=True).limit(1).execute()
    if not art_res.data:
        logger.error(f"No PublishPackage artifact found for {video_id}.")
        return
        
    publish_package = art_res.data[0]["payload"]
    title = publish_package.get("title", "Untitled Documentary")
    video_url = video.get("rendered_video_url", "")
    # Use the first thumbnail generated
    thumbnails = publish_package.get("thumbnail_urls", [])
    thumb_url = thumbnails[0] if thumbnails else ""

    message_text = (
        "📝 *SCRIPT & THUMBNAIL READY FOR RENDER*\n\n"
        f"📌 *Final Title:* {title}\n"
        f"🆔 *ID:* `{video_id}`\n\n"
        f"🖼️ [View Thumbnail Variant]({thumb_url})\n\n"
        "Click below to approve the script and trigger React Remotion:"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🎬 Approve & Render", "callback_data": f"publish:{video_id}"},
                {"text": "❌ Reject & Regenerate", "callback_data": f"reject:{video_id}"}
            ]
        ]
    }

    # Send message via Telegram Bot API
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }

    try:
        r = requests.post(tg_url, json=payload)
        if r.status_code == 200:
            # Set to pending render approval so Orchestrator waits for human callback
            sb.table("videos").update({"status": "pending_render_approval"}).eq("id", video_id).execute()
            logger.info(f"✅ Telegram publish gate dispatched for video {video_id}.")
        else:
            logger.error(f"Telegram API returned status {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")

def publish_to_youtube(video_id: str) -> bool:
    """
    Executes final publishing to YouTube channel via Google API Client, reading strictly from PublishPackage.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    sb = get_supabase()
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    if not video:
        logger.error(f"Video {video_id} not found for publishing.")
        _send_telegram_error(video_id, "Video record not found in database.")
        return False

    # Prevent duplicate publishing
    if video.get("youtube_video_id"):
        logger.info(f"Video {video_id} is already published on YouTube (ID: {video.get('youtube_video_id')}). Skipping.")
        return True

    # Get PublishPackage
    art_res = sb.table("artifacts").select("*").eq("video_id", video_id).eq("artifact_type", "PublishPackage").order("revision", desc=True).limit(1).execute()
    if not art_res.data:
        err = f"No PublishPackage artifact found for {video_id}."
        logger.error(err)
        _send_telegram_error(video_id, err)
        return False
        
    publish_package = art_res.data[0]["payload"]

    title = publish_package.get("title", "Documentary Video")[:100]
    description = publish_package.get("description", f"Documentary video: {title}")[:5000]
    tags_list = publish_package.get("tags", ["documentary", "history", "economy"])
    privacy = publish_package.get("privacy_status", "private")
    video_url = video.get("rendered_video_url", "")

    if not video_url or not os.path.exists(video_url):
        logger.error(f"No rendered_video_url found or file does not exist for video {video_id}.")
        _send_telegram_error(video_id, "No rendered video URL found locally. Was rendering completed?")
        return False

    logger.info(f"Publishing video {video_id} to YouTube via Python API: '{title}'")

    sb.table("videos").update({
        "status": "publishing",
        "updated_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", video_id).execute()

    try:
        if not os.path.exists('token.json'):
            raise Exception("token.json not found! You need to authenticate first.")
            
        creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
        youtube = build('youtube', 'v3', credentials=creds)

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags_list,
                'categoryId': '27' # Education
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(video_url, chunksize=-1, resumable=True, mimetype='video/mp4')

        logger.info("Executing YouTube upload request...")
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        response = request.execute()
        yt_id = response.get('id')
        youtube_url = f"https://www.youtube.com/watch?v={yt_id}"

        logger.info(f"✅ Video uploaded to YouTube: {youtube_url}")

        # Upload Thumbnail if available
        thumbnail_urls = publish_package.get("thumbnail_urls", [])
        if thumbnail_urls:
            try:
                import requests
                import tempfile
                thumb_url = thumbnail_urls[0]
                logger.info(f"Downloading thumbnail from {thumb_url}...")
                thumb_res = requests.get(thumb_url)
                if thumb_res.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_thumb:
                        tmp_thumb.write(thumb_res.content)
                        tmp_thumb_path = tmp_thumb.name
                    logger.info("Uploading thumbnail to YouTube...")
                    youtube.thumbnails().set(
                        videoId=yt_id,
                        media_body=MediaFileUpload(tmp_thumb_path)
                    ).execute()
                    os.remove(tmp_thumb_path)
                    logger.info("✅ Thumbnail uploaded successfully.")
                else:
                    logger.error(f"Failed to download thumbnail. Status code: {thumb_res.status_code}")
            except Exception as thumb_e:
                logger.error(f"Failed to upload thumbnail: {thumb_e}")

        sb.table("videos").update({
            "status": "published",
            "youtube_url": youtube_url,
            "youtube_video_id": yt_id,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }).eq("id", video_id).execute()

        _send_telegram_success(video_id, title, youtube_url, description, tags_list)
        return True

    except Exception as e:
        error_msg = f"Upload failed: {str(e)}"
        logger.error(error_msg)
        sb.table("videos").update({
            "status": "failed",
            "error_log": error_msg,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }).eq("id", video_id).execute()
        _send_telegram_error(video_id, error_msg)
        return False


def _send_telegram_success(video_id: str, title: str, youtube_url: str,
                           description: str, tags: list):
    """Sends a success notification — delegates to centralized notifier."""
    notify_published(video_id, title, youtube_url)


def _send_telegram_error(video_id: str, error_msg: str):
    """Sends an error notification — delegates to centralized notifier."""
    notify_step_failed(video_id, "📤 YouTube Upload", error_msg)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "publish" and len(sys.argv) > 2:
            publish_to_youtube(sys.argv[2])
        else:
            send_telegram_review_gate(cmd)
    else:
        print("Usage:")
        print("  python src/publisher.py <video_id>              # Send publish review gate")
        print("  python src/publisher.py publish <video_id>      # Upload to YouTube")


