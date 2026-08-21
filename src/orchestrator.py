#!/usr/bin/env python3
"""
Master Pipeline Orchestrator
Coordinates the end-to-end documentary video generation lifecycle:
1. Scripting (GPT-4o)
2. Narration (ElevenLabs + Timestamps)
3. Visual Assets (Pexels + Fal.ai)
4. Thumbnails (Pollinations Flux)
5. Rendering (Local Remotion)
6. Publishing (YouTube Direct OAuth)

Sends Telegram notifications at every step via notifier.py
"""

import os
import sys
import time
import logging
from typing import Optional
import requests
import subprocess
import json
from dotenv import load_dotenv
from supabase import create_client

from script_generator import process_video_scripting
from audio_generator import process_video_audio
from asset_resolver import process_video_asset_resolution
from publisher import process_video_publishing_preparation
from notifier import (
    notify_pipeline_start,
    notify_step_complete,
    notify_step_failed,
    notify_render_complete,
    notify_published,
    notify_pipeline_error,
)

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
        "--image-format=jpeg",
        "--jpeg-quality=80",
        "--concurrency=2",
        "--timeout=120000"
    ]

    logger.info(f"Running command: {' '.join(cmd)}")

    renderer_dir = os.path.join(os.getcwd(), "renderer-service")
    sb = get_supabase()
    
    try:
        res = sb.table("videos").select("script_payload").eq("id", video_id).single().execute()
        script_payload = res.data.get("script_payload") or {}
    except Exception:
        script_payload = {}

    try:
        import re
        process = subprocess.Popen(
            cmd, 
            cwd=renderer_dir, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1
        )
        
        last_pct = 0
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            
            match = re.search(r'Rendered (\d+)/(\d+)', line)
            if match:
                rendered = int(match.group(1))
                total = int(match.group(2))
                if total > 0:
                    pct = int((rendered / total) * 100)
                    if pct >= last_pct + 5:
                        last_pct = pct
                        script_payload["render_progress"] = pct
                        try:
                            sb.table("videos").update({
                                "script_payload": script_payload
                            }).eq("id", video_id).execute()
                        except Exception as e:
                            logger.error(f"Failed to update render progress: {e}")
                            
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Local render failed with error code {process.returncode}")
            return False

        logger.info(f"✅ Local render completed successfully! Saved to {out_path}")

        # Final progress update
        script_payload["render_progress"] = 100
        sb.table("videos").update({
            "status": "rendered",
            "script_payload": script_payload,
            "rendered_video_url": out_path,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }).eq("id", video_id).execute()

        return True
    except Exception as e:
        logger.error(f"Failed to execute local render: {e}")
        return False


def run_pipeline_for_video(video_id: str):
    """
    Executes all pipeline phases sequentially for a video.
    Sends a Telegram notification after every step (success or failure).
    """
    sb = get_supabase()
    logger.info(f"========== STARTING PRODUCTION RUN FOR VIDEO {video_id} ==========")

    # Fetch the video record to get the title for notifications
    try:
        res = sb.table("videos").select("*").eq("id", video_id).single().execute()
        video = res.data
        title = video.get("target_title", "Untitled") if video else "Untitled"
    except Exception as e:
        logger.error(f"Could not fetch video {video_id} from Supabase: {e}")
        notify_pipeline_error(video_id, "Φόρτωση βίντεο", str(e))
        return

    # ── Kick-off notification ──────────────────────────────────────────────
    notify_pipeline_start(video_id, title)

    # ── STEP 1: Script Generation ──────────────────────────────────────────
    logger.info(">>> STEP 1: SCRIPT GENERATION (GPT-4o)...")
    try:
        process_video_scripting(video_id)
        # Re-fetch to get the generated title (GPT-4o may refine it)
        res = sb.table("videos").select("target_title, script_payload").eq("id", video_id).single().execute()
        updated = res.data or {}
        title = updated.get("target_title", title)
        scene_count = len((updated.get("script_payload") or {}).get("scenes", []))
        notify_step_complete(video_id, "✍️ Script Generation (GPT-4o)", f"{scene_count} σκηνές | Τίτλος: {title}")
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        notify_step_failed(video_id, "✍️ Script Generation", str(e))
        notify_pipeline_error(video_id, "Script Generation", str(e))
        return

    # ── STEP 2: Audio & Timestamps ─────────────────────────────────────────
    logger.info(">>> STEP 2: AUDIO & TIMESTAMPS (ElevenLabs)...")
    try:
        process_video_audio(video_id)
        res = sb.table("videos").select("transcript_timestamps").eq("id", video_id).single().execute()
        ts = (res.data or {}).get("transcript_timestamps") or {}
        duration = ts.get("total_duration_seconds", 0)
        notify_step_complete(video_id, "🎙️ Audio Generation (ElevenLabs)", f"Διάρκεια: {duration:.1f}s")
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        notify_step_failed(video_id, "🎙️ Audio Generation", str(e))
        notify_pipeline_error(video_id, "Audio Generation", str(e))
        return

    # ── STEP 3: Visual Assets ──────────────────────────────────────────────
    logger.info(">>> STEP 3: VISUAL ASSET SOURCING (Pexels + Fal.ai)...")
    try:
        process_video_asset_resolution(video_id)
        res = sb.table("videos").select("script_payload").eq("id", video_id).single().execute()
        scenes = ((res.data or {}).get("script_payload") or {}).get("scenes", [])
        stock = sum(1 for s in scenes if s.get("asset_type") == "video")
        ai_imgs = sum(1 for s in scenes if s.get("asset_type") == "image")
        notify_step_complete(video_id, "🖼️ Visual Assets (Pexels + Fal.ai)", f"{stock} stock video | {ai_imgs} AI images")
    except Exception as e:
        logger.error(f"Asset resolution failed: {e}")
        notify_step_failed(video_id, "🖼️ Visual Assets", str(e))
        notify_pipeline_error(video_id, "Visual Assets", str(e))
        return

    # ── STEP 4: Thumbnails ─────────────────────────────────────────────────
    logger.info(">>> STEP 4: GENERATING THUMBNAILS (Pollinations Flux)...")
    try:
        process_video_publishing_preparation(video_id)
        notify_step_complete(video_id, "🖼️ Thumbnails (Pollinations Flux)", "2 candidates δημιουργήθηκαν")
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        notify_step_failed(video_id, "🖼️ Thumbnails", str(e))
        # Non-fatal: continue pipeline even if thumbnails fail

    # ── Fetch full video state for render ─────────────────────────────────
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    # ── STEP 5: Remotion Local Render ─────────────────────────────────────
    logger.info(">>> STEP 5: RENDERING VIDEO LOCALLY (Remotion)...")
    input_props = prepare_remotion_props(video)
    render_success = execute_local_remotion_render(video_id, input_props)

    if not render_success:
        notify_step_failed(video_id, "🎬 Remotion Render", "Render απέτυχε — έλεγξε τα logs.")
        notify_pipeline_error(video_id, "Remotion Render", "subprocess exited with non-zero code")
        return

    video_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"
    ts_data = video.get("transcript_timestamps") or {}
    duration = ts_data.get("total_duration_seconds", 0)
    notify_render_complete(video_id, video_path, f"{duration:.0f}s")

    # ── STEP 6: YouTube Upload (via n8n Webhook) ─────────────────────────────
    logger.info(">>> STEP 6: UPLOADING TO YOUTUBE (via n8n Webhook)...")
    try:
        from publisher import publish_to_youtube
        
        success = publish_to_youtube(video_id)
        if success:
            logger.info("✅ Upload step completed successfully via n8n gateway.")
        else:
            logger.error("❌ Upload step failed.")
            notify_step_failed(video_id, "📤 YouTube Upload", "Upload failed.")
            notify_pipeline_error(video_id, "YouTube Upload", "Upload failed.")
            return
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        notify_step_failed(video_id, "📤 YouTube Upload", str(e))
        notify_pipeline_error(video_id, "YouTube Upload", str(e))
        return

    logger.info(f"========== PRODUCTION RUN COMPLETED FOR VIDEO {video_id} ==========")


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
                run_pipeline_for_video(str(target["id"]))
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
