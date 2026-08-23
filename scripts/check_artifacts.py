import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
video_id = "018dad84-9501-400e-ba31-caa084f403bd"

res = sb.table("artifacts").select("artifact_type, payload").eq("video_id", video_id).eq("artifact_type", "EditedStoryScript").order("revision", desc=True).limit(1).execute()

if res.data:
    content = json.dumps(res.data[0]["payload"], indent=2)
    print(content)
else:
    print("No EditedStoryScript found")
