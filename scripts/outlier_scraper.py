#!/usr/bin/env python3
"""
Outlier Scraper Module
Scrapes competitor YouTube channels, calculates median performance metrics,
and surfaces viral outliers (>= 3.0x median views & >= 15,000 views).
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import yt_dlp
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def get_supabase_client() -> Optional[Client]:
    if not SUPABASE_SERVICE_KEY:
        logger.warning("SUPABASE_SERVICE_ROLE_KEY not set. Operating in offline/dry-run mode.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def evaluate_channel_outliers(
    channel_url: str,
    sample_size: int = 20,
    multiplier_threshold: float = 3.0,
    min_views_threshold: int = 15000
) -> Dict[str, Any]:
    """
    Evaluates recent videos of a channel, calculates median views,
    and returns outlier videos exceeding threshold multipliers.
    """
    ydl_opts = {
        'extract_flat': False,
        'playlist_items': f'1-{sample_size}',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'ignoreerrors': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }

    # Normalize channel URL to the /videos tab to fetch full video entries
    normalized_url = channel_url.rstrip('/')
    if not normalized_url.endswith('/videos') and not '/watch?' in normalized_url:
        normalized_url = f"{normalized_url}/videos"

    logger.info(f"Extracting recent {sample_size} videos from: {normalized_url}")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(normalized_url, download=False)
        except Exception as e:
            logger.error(f"Failed to fetch info for channel {channel_url}: {e}")
            return {"channel_name": "Unknown", "median_views": 0, "outliers": []}

    entries = info.get('entries', []) if info else []
    channel_name = info.get('channel') or info.get('uploader') or info.get('title') or "Unknown Channel"
    channel_id = info.get('channel_id') or info.get('id') or channel_url

    if len(entries) < 5:
        logger.warning(f"Channel {channel_name} has fewer than 5 recent videos ({len(entries)}). Skipping.")
        return {"channel_name": channel_name, "channel_id": channel_id, "median_views": 0, "outliers": []}

    views = [e.get('view_count', 0) for e in entries if e.get('view_count') is not None]
    if not views:
        logger.warning(f"No view count data available for channel {channel_name}.")
        return {"channel_name": channel_name, "channel_id": channel_id, "median_views": 0, "outliers": []}

    median_views = float(np.median(views))
    logger.info(f"Channel: '{channel_name}' | Analyzed {len(entries)} videos | Median Views: {int(median_views):,}")

    outliers = []
    for entry in entries:
        v_count = entry.get('view_count', 0) or 0
        multiplier = v_count / median_views if median_views > 0 else 0

        if multiplier >= multiplier_threshold and v_count >= min_views_threshold:
            outlier_data = {
                "video_id": entry.get('id'),
                "title": entry.get('title', 'Untitled'),
                "views": v_count,
                "median": int(median_views),
                "multiplier": round(multiplier, 2),
                "url": f"https://youtube.com/watch?v={entry.get('id')}",
                "description": entry.get('description', '')[:500] if entry.get('description') else '',
                "channel_name": channel_name,
                "channel_id": channel_id
            }
            outliers.append(outlier_data)
            logger.info(
                f"🔥 OUTLIER FOUND: [{multiplier:.1f}x] '{outlier_data['title']}' "
                f"({v_count:,} views vs median {int(median_views):,})"
            )

    return {
        "channel_name": channel_name,
        "channel_id": channel_id,
        "median_views": int(median_views),
        "outliers": outliers
    }


def sync_outliers_to_supabase(results: Dict[str, Any], client: Client) -> int:
    """
    Saves new outliers into the Supabase 'videos' queue and updates 'monitored_channels'.
    """
    channel_id = results.get("channel_id")
    channel_name = results.get("channel_name")
    median_views = results.get("median_views", 0)
    outliers = results.get("outliers", [])

    # Update or insert channel in monitored_channels
    if channel_id and channel_name:
        try:
            client.table("monitored_channels").upsert({
                "channel_id": channel_id,
                "channel_name": channel_name,
                "median_views": median_views
            }, on_conflict="channel_id").execute()
        except Exception as e:
            logger.error(f"Error updating monitored_channels: {e}")

    inserted_count = 0
    for item in outliers:
        video_id = item.get("video_id")
        title = item.get("title")

        # Check if video already exists in database
        try:
            existing = client.table("videos").select("id").eq("source_video_id", video_id).execute()
            if existing.data and len(existing.data) > 0:
                logger.info(f"Video {video_id} already exists in database. Skipping duplicate.")
                continue

            # Insert new outlier into queue
            res = client.table("videos").insert({
                "source_type": "outlier_scraped",
                "source_video_id": video_id,
                "target_title": title,
                "topic_premise": f"Viral outlier from channel '{channel_name}' ({item['multiplier']}x median views): {title}",
                "status": "discovered"
            }).execute()

            if res.data:
                inserted_count += 1
                logger.info(f"✅ Queued outlier in Supabase: '{title}' (ID: {res.data[0]['id']})")
        except Exception as e:
            logger.error(f"Failed to insert video {video_id} to Supabase: {e}")

    return inserted_count


def scan_all_monitored_channels():
    """
    Scans all channels registered in the 'monitored_channels' table.
    """
    client = get_supabase_client()
    if not client:
        logger.error("Supabase client not initialized. Cannot fetch monitored channels.")
        return

    try:
        response = client.table("monitored_channels").select("*").execute()
        channels = response.data or []
    except Exception as e:
        logger.error(f"Failed to fetch monitored channels: {e}")
        return

    if not channels:
        logger.warning("No channels found in 'monitored_channels'. Add channels first with manage_channels.py.")
        return

    logger.info(f"Found {len(channels)} monitored channel(s). Starting outlier scan...")
    total_new_outliers = 0

    for ch in channels:
        ch_url = f"https://www.youtube.com/channel/{ch['channel_id']}" if not ch['channel_id'].startswith("http") else ch['channel_id']
        result = evaluate_channel_outliers(ch_url)
        inserted = sync_outliers_to_supabase(result, client)
        total_new_outliers += inserted

    logger.info(f"Scan complete. Total new outliers queued: {total_new_outliers}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Direct URL scan
        target_url = sys.argv[1]
        logger.info(f"Running standalone scan on URL: {target_url}")
        res = evaluate_channel_outliers(target_url)
        sb_client = get_supabase_client()
        if sb_client:
            sync_outliers_to_supabase(res, sb_client)
        else:
            logger.info(f"Results: {res}")
    else:
        # Batch scan of all monitored channels
        scan_all_monitored_channels()
