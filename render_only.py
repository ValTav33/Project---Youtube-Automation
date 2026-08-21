import os
import sys
import logging

sys.path.append("src")
from orchestrator import prepare_remotion_props, execute_local_remotion_render, get_supabase, notify_render_complete, notify_step_failed
from publisher import publish_to_youtube

video_id = "df6b22cc-bcf7-49d2-a4de-3ab51a69b198"
sb = get_supabase()
res = sb.table("videos").select("*").eq("id", video_id).single().execute()
video = res.data

if not video:
    print("Video not found")
    sys.exit(1)

input_props = prepare_remotion_props(video)
print(f"Starting render for video {video_id}...")
render_success = execute_local_remotion_render(video_id, input_props)

if render_success:
    video_path = f"/Users/valsamis/Movies/Automated/{video_id}.mp4"
    ts_data = video.get("transcript_timestamps") or {}
    duration = ts_data.get("total_duration_seconds", 0)
    notify_render_complete(video_id, video_path, f"{duration:.0f}s")
    print("Render succeeded! Proceeding to upload.")
    
    try:
        if publish_to_youtube(video_id):
            print("Upload succeeded")
        else:
            print("Upload failed")
    except Exception as e:
        print(f"Upload exception: {e}")
else:
    print("Render failed.")
