import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
res = sb.table("videos").select("id, status, target_title").eq("id", "e720f67c-34f3-4cac-a299-8767804bcac5").execute()
print(res.data)
