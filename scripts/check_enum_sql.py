import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
res = sb.table("videos").select("*").limit(1).execute()
print("Checking schema is not easy without psql, but we can query pg_type")
res = sb.rpc("get_enum_values", {"enum_name": "video_status"}).execute()
print(res.data)
