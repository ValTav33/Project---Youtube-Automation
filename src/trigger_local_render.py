import sys
import time
from orchestrator import execute_local_remotion_render, get_supabase, prepare_remotion_props, logger

if len(sys.argv) < 2:
    print("Provide video id")
    sys.exit(1)

video_id = sys.argv[1]
sb = get_supabase()

res = sb.table("videos").select("*").eq("id", video_id).single().execute()
video = res.data

logger.info(">>> RENDERING VIDEO LOCALLY...")
input_props = prepare_remotion_props(video)
render_success = execute_local_remotion_render(video_id, input_props)

if render_success:
    logger.info(">>> UPLOADING TO YOUTUBE...")
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
    logger.error("Local render failed!")
