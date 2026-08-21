import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client
from youtube_auth import get_authenticated_service

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def ingest_analytics():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase credentials missing.")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # 1. Get videos that are published and have a youtube_video_id
    res = sb.table("videos").select("id, youtube_video_id").not_.is_("youtube_video_id", "null").execute()
    published_videos = res.data

    if not published_videos:
        logger.info("No published videos found to ingest analytics for.")
        return

    try:
        # Initialize APIs
        youtube_data = get_authenticated_service('youtube', 'v3')
        youtube_analytics = get_authenticated_service('youtubeAnalytics', 'v2')
    except Exception as e:
        logger.error(f"Failed to authenticate with YouTube: {e}")
        return

    for video in published_videos:
        video_id = video["id"]
        yt_id = video["youtube_video_id"]

        logger.info(f"Fetching analytics for video {video_id} (YT: {yt_id})")

        try:
            # 1. Fetch from YouTube Data API (Views, Likes, Comments)
            video_request = youtube_data.videos().list(
                part="statistics",
                id=yt_id
            )
            video_response = video_request.execute()

            if not video_response.get("items"):
                logger.warning(f"Video {yt_id} not found on YouTube.")
                continue

            stats = video_response["items"][0]["statistics"]
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            
            impressions = 0
            ctr = 0.0
            avg_view_duration = 0
            avg_percent_viewed = 0.0
            subs_gained = 0

            # Insert snapshot
            sb.table("youtube_analytics_snapshots").insert({
                "video_id": video_id,
                "youtube_video_id": yt_id,
                "views": views,
                "likes": likes,
                "comments": comments,
                "impressions": impressions,
                "click_through_rate": ctr,
                "average_view_duration": avg_view_duration,
                "average_percentage_viewed": avg_percent_viewed,
                "subscribers_gained": subs_gained
            }).execute()

            logger.info(f"Saved snapshot for {yt_id}: {views} views, {likes} likes")

        except Exception as e:
            logger.error(f"Error fetching analytics for {yt_id}: {e}")

if __name__ == "__main__":
    ingest_analytics()
