import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
res = sb.table("artifacts").select("payload").eq("video_id", "483cd459-5e09-42d7-aacf-f132387ed545").eq("artifact_type", "RendererManifest").order("revision", desc=True).limit(1).execute()
payload = res.data[0]["payload"]["payload"]
words = payload.get("words", [])
if words:
    print(f"Total words: {len(words)}")
    print(f"Last word end time: {words[-1].get('end')}")
