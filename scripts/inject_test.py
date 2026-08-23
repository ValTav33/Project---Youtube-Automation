import os
import uuid
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

video_id = str(uuid.uuid4())
video_data = {
    "id": video_id,
    "source_type": "manual_telegram",
    "target_title": "The 60-Second History of Coffee",
    "topic_premise": "A very fast-paced, 60-second summary of how coffee was discovered. CRITICAL REQUIREMENT: The entire script MUST be extremely short. Keep the total word count under 150 words to ensure the video is under 1 minute.",
    "status": "approved"
}

print(f"Injecting video row with ID: {video_id} and topic: {video_data['target_title']}")
sb.table("videos").insert(video_data).execute()
print("Success! Orchestrator will now pick it up and run the pipeline.")
