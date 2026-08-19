#!/usr/bin/env python3
"""
Master Pipeline Orchestrator
Coordinates the end-to-end documentary video generation lifecycle:
1. Scripting (GPT-4o)
2. Narration (ElevenLabs + Timestamps)
3. Visual Assets (Pexels + Fal.ai)
4. Rendering (Railway Remotion Microservice)
5. Review Gate & Publishing (Thumbnails + Telegram)
"""

import os
import sys
import time
import logging
from typing import Optional
import requests
from dotenv import load_dotenv
from supabase import create_client

from script_generator import process_video_scripting
from audio_generator import process_video_audio
from asset_resolver import process_video_asset_resolution
from publisher import process_video_publishing_preparation

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
REMOTION_RENDERER_URL = os.getenv("REMOTION_RENDERER_URL", "http://localhost:3000")
FPS = 30


def get_supabase():
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def prepare_remotion_props(video_data: dict) -> dict:
    """
    Computes scene frame durations and bundles props for Remotion renderer.
    """
    script_payload = video_data.get("script_payload", {})
    scenes = script_payload.get("scenes", [])
    timestamps_data = video_data.get("transcript_timestamps", {})
    words = timestamps_data.get("words", [])
    total_audio_duration = timestamps_data.get("total_duration_seconds", 0)
    audio_url = video_data.get("audio_url", "")

    # Calculate proportional duration per scene
    total_words = sum(len(s.get("narration", "").split()) for s in scenes) or 1
    remotion_scenes = []

    for scene in scenes:
        scene_word_count = len(scene.get("narration", "").split())
        ratio = scene_word_count / total_words
        scene_seconds = max(ratio * total_audio_duration, 4.0)
        frames = int(scene_seconds * FPS)

        remotion_scenes.append({
            "scene_id": scene.get("scene_id"),
            "durationInFrames": frames,
            "asset_type": scene.get("asset_type", "image"),
            "asset_url": scene.get("asset_url", ""),
            "narration": scene.get("narration", ""),
            "visual_overlay": scene.get("visual_overlay")
        })

    return {
        "scenes": remotion_scenes,
        "words": words,
        "audioUrl": audio_url,
        "bgMusicUrl": "",
        "bgMusicVolume": 0.12
    }


def trigger_remotion_render(video_id: str, input_props: dict) -> bool:
    """
    Dispatches rendering request to Remotion microservice.
    """
    url = f"{REMOTION_RENDERER_URL}/api/render"
    payload = {
        "videoId": video_id,
        "inputProps": input_props
    }

    logger.info(f"Dispatching render request for video {video_id} to {url}...")
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code in (200, 202):
            logger.info(f"✅ Render job successfully queued with microservice.")
            return True
        else:
            logger.error(f"Microservice returned status {r.status_code}: {r.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to reach Remotion renderer service at {url}: {e}")
        return False


def run_pipeline_for_video(video_id: str):
    """
    Executes all pipeline phases sequentially for an approved video.
    """
    sb = get_supabase()
    logger.info(f"========== STARTING PRODUCTION RUN FOR VIDEO {video_id} ==========")

    # Step 1: Scripting
    logger.info(">>> STEP 1: SCRIPT GENERATION (GPT-4o)...")
    process_video_scripting(video_id)

    # Step 2: Audio & Timestamps
    logger.info(">>> STEP 2: AUDIO & TIMESTAMPS (ElevenLabs)...")
    process_video_audio(video_id)

    # Step 3: Visual Assets
    logger.info(">>> STEP 3: VISUAL ASSET SOURCING (Pexels + Fal.ai)...")
    process_video_asset_resolution(video_id)

    # Fetch updated video state
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    # Step 4: Generate Thumbnails (Pollinations Flux)
    logger.info(">>> STEP 4: GENERATING 16:9 THUMBNAILS...")
    process_video_publishing_preparation(video_id)

    # Fetch updated video state for renderer
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    # Step 5: Dispatch Render to Railway Remotion Microservice
    logger.info(">>> STEP 5: PREPARING & DISPATCHING REMOTION RENDER JOB...")
    input_props = prepare_remotion_props(video)
    render_dispatched = trigger_remotion_render(video_id, input_props)

    if not render_dispatched:
        logger.warning("Render service was not reachable. Video assets and props are ready in Supabase.")

    logger.info(f"========== PRODUCTION DISPATCH COMPLETED FOR VIDEO {video_id} ==========")


def poll_approved_queue():
    """
    Polls the Supabase videos table for any videos with status 'approved' and processes them.
    """
    sb = get_supabase()
    logger.info("Starting production queue poller (watching for 'approved' status)...")

    while True:
        try:
            res = sb.table("videos").select("id, target_title").eq("status", "approved").limit(1).execute()
            rows = res.data or []
            if rows:
                target = rows[0]
                logger.info(f"Found approved video in queue: '{target['target_title']}' (ID: {target['id']})")
                run_pipeline_for_video(target["id"])
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Stopping poller.")
            break
        except Exception as e:
            logger.error(f"Error in queue poller loop: {e}")
            time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_arg = sys.argv[1]
        if target_arg == "poll":
            poll_approved_queue()
        else:
            run_pipeline_for_video(target_arg)
    else:
        print("Usage:")
        print("  python src/orchestrator.py <video_id>   # Run pipeline for specific video")
        print("  python src/orchestrator.py poll         # Poll queue for approved videos")
