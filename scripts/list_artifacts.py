import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
res = sb.table("artifacts").select("artifact_type").eq("video_id", "483cd459-5e09-42d7-aacf-f132387ed545").execute()
print([x["artifact_type"] for x in res.data])
