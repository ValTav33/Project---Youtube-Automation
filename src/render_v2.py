#!/usr/bin/env python3
import sys
import os
import time
import json
import logging
import subprocess
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def execute_render_v2(video_id: str):
    logger.info(f"Starting V2 Render for video {video_id}...")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase credentials missing.")
        return False

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. Fetch RendererManifest
    res = sb.table("artifacts").select("payload").eq("video_id", video_id).eq("artifact_type", "RendererManifest").order("revision", desc=True).limit(1).execute()
    if not res.data:
        logger.error(f"No RendererManifest found for video {video_id}.")
        return False
        
    manifest_dump = res.data[0].get("payload", {})
    if not manifest_dump or "payload" not in manifest_dump:
        logger.error("RendererManifest payload is empty or malformed.")
        return False
        
    # The artifact's payload column contains the full RendererManifest dump.
    # The actual Remotion props are inside the 'payload' field of the manifest.
    props = manifest_dump["payload"]
        
    logger.info("Successfully fetched RendererManifest.")
    
    # 2. Write props to /tmp/
    props_path = f"/tmp/props_{video_id}.json"
    with open(props_path, "w") as f:
        json.dump(props, f)
        
    out_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # 3. Execute Remotion Render
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
                        # V2 doesn't use script_payload for render progress, but we can update video status directly
                        logger.info(f"Render progress: {pct}%")
                            
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Local render failed with error code {process.returncode}")
            return False

        logger.info(f"✅ Local render completed successfully! Saved to {out_path}")
        
        # 4. Update Video Status
        sb.table("videos").update({
            "status": "rendered",
            "rendered_video_url": out_path,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
        }).eq("id", video_id).execute()
        
        # 5. YouTube Upload
        logger.info(">>> UPLOADING TO YOUTUBE...")
        try:
            from youtube_uploader import upload_video
            
            vid_res = sb.table("videos").select("*").eq("id", video_id).single().execute()
            video = vid_res.data
            title = video.get("target_title", "Documentary")
            
            # Extract desc and tags from PublishPackage
            pub_res = sb.table("artifacts").select("payload").eq("video_id", video_id).eq("artifact_type", "PublishPackage").order("revision", desc=True).limit(1).execute()
            
            desc = f"Documentary about {title}"
            tags = ["documentary"]
            
            if pub_res.data and pub_res.data[0].get("payload"):
                pub_payload = pub_res.data[0].get("payload")
                desc = pub_payload.get("description", desc)
                tags = pub_payload.get("tags", tags)
                
            yt_id = upload_video(out_path, title, desc, tags, privacy_status="unlisted")
            
            sb.table("videos").update({
                "status": "published",
                "youtube_url": f"https://youtu.be/{yt_id}",
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")
            }).eq("id", video_id).execute()
            
            logger.info(f"✅ Video successfully published! URL: https://youtu.be/{yt_id}")
            
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            # Do not return False here, the render succeeded at least
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to execute local render: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_render_v2(sys.argv[1])
    else:
        print("Usage: python src/render_v2.py <video_id>")
