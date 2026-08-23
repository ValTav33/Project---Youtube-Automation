import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
video_id = "483cd459-5e09-42d7-aacf-f132387ed545"

# Delete artifacts
sb.table("artifacts").delete().eq("video_id", video_id).execute()
# Delete pipeline runs
sb.table("pipeline_runs").delete().eq("video_id", video_id).execute()

# Reset status to approved
sb.table("videos").update({"status": "approved"}).eq("id", video_id).execute()
print("Pipeline reset successful for video:", video_id)
