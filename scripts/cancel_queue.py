import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
active_status = ["approved", "scripting", "awaiting_publish_approval"]

res = sb.table("videos").select("id, target_title, status").in_("status", active_status).execute()
kept_id = "018dad84-9501-400e-ba31-caa084f403bd"

deleted = 0
for v in res.data:
    if v["id"] != kept_id:
        print(f"Cancelling video: {v['target_title']} (ID: {v['id']})")
        sb.table("videos").update({"status": "failed", "error_log": "Cancelled by user"}).eq("id", v["id"]).execute()
        deleted += 1

print(f"Cancelled {deleted} videos.")
