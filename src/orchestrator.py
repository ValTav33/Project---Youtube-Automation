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

from publisher import send_telegram_review_gate, publish_to_youtube
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


def prepare_remotion_props(video_id: str) -> dict:
    """
    Fetches the RendererManifest artifact from Supabase which contains the pre-computed Remotion props.
    """
    sb = get_supabase()
    res = sb.table("artifacts").select("payload").eq("video_id", video_id).eq("artifact_type", "RendererManifest").order("revision", desc=True).limit(1).execute()
    
    if not res.data:
        logger.error(f"No RendererManifest found for video {video_id}. Cannot render.")
        return {}
        
    return res.data[0]["payload"]


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




def run_render_phase(video_id: str):
    """
    Executes the rendering and publishing phases for a video after human approval.
    """
    sb = get_supabase()
    logger.info(f"========== STARTING RENDER PHASE FOR VIDEO {video_id} ==========")

    # ── Fetch full video state for render ─────────────────────────────────
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    if not video:
        logger.error(f"Video {video_id} not found.")
        return

    # ── STEP 5: Remotion Local Render ─────────────────────────────────────
    logger.info(">>> STEP 5: RENDERING VIDEO LOCALLY (Remotion)...")
    input_props = prepare_remotion_props(video_id)
    render_success = execute_local_remotion_render(video_id, input_props)

    if not render_success:
        notify_step_failed(video_id, "🎬 Remotion Render", "Render απέτυχε — έλεγξε τα logs.")
        notify_pipeline_error(video_id, "Remotion Render", "subprocess exited with non-zero code")
        return

    video_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"
    ts_data = video.get("transcript_timestamps") or {}
    duration = ts_data.get("total_duration_seconds", 0)
    notify_render_complete(video_id, video_path, f"{duration:.0f}s")

    # ── STEP 6: YouTube Upload (via n8n Webhook or Python API) ─────────────
    logger.info(">>> STEP 6: UPLOADING TO YOUTUBE...")
    try:
        success = publish_to_youtube(video_id)
        if success:
            logger.info("✅ Upload step completed successfully.")
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

    logger.info(f"========== FULL PIPELINE COMPLETED FOR VIDEO {video_id} ==========")


def poll_approved_queue():
    """
    Polls the Supabase videos table for generation and render queues.
    """
    sb = get_supabase()
    logger.info("Starting production queue poller (watching for 'approved' & 'awaiting_publish_approval')...")

    while True:
        try:
            # Check for generation tasks
            res = sb.table("videos").select("id, target_title").eq("status", "approved").limit(1).execute()
            rows = res.data or []
            if rows:
                from run_v2 import run_v2_story_pipeline
                target = rows[0]
                logger.info(f"Found approved video for generation: '{target['target_title']}' (ID: {target['id']})")
                run_v2_story_pipeline(str(target["id"]))
            
            # Check for render tasks
            res2 = sb.table("videos").select("id, target_title").eq("status", "awaiting_publish_approval").limit(1).execute()
            rows2 = res2.data or []
            if rows2:
                target2 = rows2[0]
                logger.info(f"Found video approved for render: '{target2['target_title']}' (ID: {target2['id']})")
                run_render_phase(str(target2["id"]))

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
