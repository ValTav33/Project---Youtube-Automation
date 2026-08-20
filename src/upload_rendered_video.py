import os
import sys
import time
import logging

# Ensure project root & src are in path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from orchestrator import get_supabase
from youtube_uploader import upload_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

video_id = "47b043a7-65b7-4238-9e0f-eaf038864640"
video_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"

if not os.path.exists(video_path):
    logger.error(f"Video file not found at {video_path}")
    sys.exit(1)

sb = get_supabase()
res = sb.table("videos").select("*").eq("id", video_id).single().execute()
video = res.data

title = video.get("target_title", "Documentary")
script_meta = video.get("script_payload", {}).get("meta", {})
desc = script_meta.get("description", f"Documentary about {title}")
tags = script_meta.get("tags", ["documentary"])

logger.info(f"Uploading video {video_id} to YouTube...")
logger.info(f"Title: {title}")
logger.info(f"Description length: {len(desc)} characters")
logger.info(f"Tags: {tags}")

try:
    yt_id = upload_video(video_path, title, desc, tags, privacy_status="unlisted")
    
    youtube_url = f"https://youtu.be/{yt_id}"
    sb.table("videos").update({
        "status": "published",
        "youtube_url": youtube_url,
        "youtube_video_id": yt_id,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }).eq("id", video_id).execute()
    
    logger.info(f"🎉 SUCCESS! Video successfully uploaded to YouTube: {youtube_url}")
    print(f"\n==========================================")
    print(f"🎉 VIDEO PUBLISHED: {youtube_url}")
    print(f"==========================================\n")
except Exception as e:
    logger.error(f"Failed to upload to YouTube: {e}")
    sys.exit(1)
