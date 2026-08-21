#!/usr/bin/env python3
"""
Publishing & Feedback Loop Engine
- Generates high-CTR thumbnails using Pollinations Flux (free, no key required)
- Publishes videos to YouTube channel via YouTube Data API v3 or n8n webhook
- Uses centralized notifier.py for all Telegram notifications
"""

import os
import sys
import time
import logging
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv
from supabase import create_client
from notifier import notify_step_failed

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FAL_KEY = os.getenv("FAL_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def get_supabase():
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def generate_thumbnails(topic: str, count: int = 2) -> List[str]:
    """
    Generates high-CTR 16:9 YouTube thumbnails via Pollinations Flux (100% free, zero-key required)
    and uploads them to Supabase Storage.
    """
    import urllib.parse
    sb = get_supabase()

    thumbnail_prompt = (
        f"YouTube thumbnail graphic, dramatic cinematic lighting, central subject, "
        f"high vibrancy, clean silhouette, 8k resolution, minimalist hyper-focus: {topic}"
    )

    thumbnails = []
    logger.info(f"Generating {count} thumbnail candidate(s) via Free Flux Engine for: '{topic}'...")

    for i in range(count):
        try:
            encoded_prompt = urllib.parse.quote(f"{thumbnail_prompt}, variant {i+1}")
            pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&model=flux&seed={i * 42 + 7}"

            resp = requests.get(pollinations_url, timeout=25)
            if resp.status_code == 200 and len(resp.content) > 1000:
                storage_filename = f"thumb_{int(time.time())}_{i+1}.jpg"
                sb.storage.from_("thumbnails").upload(
                    path=storage_filename,
                    file=resp.content,
                    file_options={"content-type": "image/jpeg", "upsert": "true"}
                )
                public_url = sb.storage.from_("thumbnails").get_public_url(storage_filename)
                thumbnails.append(public_url)
                logger.info(f"✅ Thumbnail #{i+1} saved to Supabase: {public_url}")
            else:
                thumbnails.append(pollinations_url)
        except Exception as e:
            logger.error(f"Thumbnail generation error on candidate #{i+1}: {e}")

    return thumbnails or [
        "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1280&q=80"
    ]


def send_telegram_review_gate(video_id: str):
    """
    Dispatches a Telegram review card with preview link, thumbnails, and 1-click publish button.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram bot credentials not configured. Skipping review gate.")
        return

    sb = get_supabase()
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data
    if not video:
        logger.error(f"Video {video_id} not found.")
        return

    title = video.get("target_title", "Untitled Documentary")
    video_url = video.get("rendered_video_url", "")
    thumbnails = video.get("thumbnail_urls", [])

    message_text = (
        f"🎬 *VIDEO PRODUCTION READY FOR REVIEW*\n\n"
        f"📌 *Title:* {title}\n"
        f"🆔 *ID:* `{video_id}`\n\n"
        f"🔗 [Watch Rendered Video Preview]({video_url})\n\n"
        f"Click below to approve and publish immediately to YouTube:"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚀 Approve & Publish", "callback_data": f"publish:{video_id}"},
                {"text": "❌ Reject", "callback_data": f"reject:{video_id}"}
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
            logger.info(f"✅ Telegram review gate dispatched for video {video_id}.")
        else:
            logger.error(f"Telegram API returned status {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")


def process_video_publishing_preparation(video_id: str):
    """
    Generates thumbnails and persists them to Supabase.
    Notifications are handled by orchestrator via notifier.py.
    """
    sb = get_supabase()
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    if not video:
        return

    topic = video.get("target_title", "")
    thumbnails = generate_thumbnails(topic)

    sb.table("videos").update({
        "thumbnail_urls": thumbnails
    }).eq("id", video_id).execute()

def publish_to_youtube(video_id: str) -> bool:
    """
    Executes final publishing to YouTube channel via Google API Client.
    """
    import datetime
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

    title = video.get("target_title", "Documentary Video")[:100]
    script_meta = video.get("script_payload", {}).get("meta", {})
    description = script_meta.get("description", f"Documentary video: {title}")[:5000]
    tags_list = script_meta.get("tags", ["documentary", "history", "economy"])
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
                'privacyStatus': 'private', # Default to private for review
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
    from notifier import notify_published
    notify_published(video_id, title, youtube_url)


def _send_telegram_error(video_id: str, error_msg: str):
    """Sends an error notification — delegates to centralized notifier."""
    notify_step_failed(video_id, "📤 YouTube Upload (n8n)", error_msg)


if __name__ == "__main__":
    import time
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "publish" and len(sys.argv) > 2:
            publish_to_youtube(sys.argv[2])
        else:
            process_video_publishing_preparation(cmd)
    else:
        print("Usage:")
        print("  python src/publisher.py <video_id>              # Generate thumbnails + review gate")
        print("  python src/publisher.py publish <video_id>      # Upload to YouTube via n8n")

