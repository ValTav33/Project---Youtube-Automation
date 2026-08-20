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
import subprocess
import json
import time
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


def execute_local_remotion_render(video_id: str, input_props: dict) -> bool:
    """
    Executes Remotion directly on the local machine via subprocess.
    """
    logger.info(f"Starting local Remotion render for video {video_id}...")
    
    # Save input_props to a temp file
    props_path = f"/tmp/props_{video_id}.json"
    with open(props_path, "w") as f:
        json.dump(input_props, f)
        
    out_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # Run npx remotion render
    cmd = [
        "npx", "remotion", "render", 
        "src/index.ts", "MainVideo", out_path,
        f"--props={props_path}",
        "--concurrency=2"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    renderer_dir = os.path.join(os.getcwd(), "renderer-service")
    try:
        subprocess.run(cmd, cwd=renderer_dir, check=True)
        logger.info(f"✅ Local render completed successfully! Saved to {out_path}")
        
        # Update database with local path
        sb = get_supabase()
        sb.table("videos").update({
            "status": "rendered",
            "rendered_video_url": out_path,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }).eq("id", video_id).execute()
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Local render failed with error code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Failed to execute local render: {e}")
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

    # Step 5: Render Video Locally
    logger.info(">>> STEP 5: RENDERING VIDEO LOCALLY...")
    input_props = prepare_remotion_props(video)
    render_success = execute_local_remotion_render(video_id, input_props)

    if render_success:
        logger.info(">>> STEP 6: UPLOADING TO YOUTUBE...")
        try:
            from youtube_uploader import upload_video
            
            title = video.get("target_title", "Documentary")
            script_meta = video.get("script_payload", {}).get("meta", {})
            desc = script_meta.get("description", f"Documentary about {title}")
            tags = script_meta.get("tags", ["documentary"])
            video_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"
            
            yt_id = upload_video(video_path, title, desc, tags, privacy_status="unlisted")
            
            sb.table("videos").update({
                "status": "published",
                "youtube_url": f"https://youtu.be/{yt_id}",
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
            }).eq("id", video_id).execute()
            
            logger.info(f"✅ Video successfully published! URL: https://youtu.be/{yt_id}")
            
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
    else:
        logger.warning("Local render failed. Upload aborted.")

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
