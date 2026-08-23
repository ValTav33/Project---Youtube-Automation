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
    "target_title": "The Forgotten Empire of Tartaria",
    "topic_premise": "Was Tartaria a real advanced global empire that was erased from history by a mud flood, or just a cartographical misunderstanding?",
    "status": "approved"
}

print(f"Injecting video row with ID: {video_id} and topic: {video_data['target_title']}")
sb.table("videos").insert(video_data).execute()
print("Success! Orchestrator will now pick it up and run the pipeline.")
