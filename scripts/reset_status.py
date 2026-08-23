import os
import sys
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
sb.table("videos").update({"status": "awaiting_publish_approval"}).eq("id", "483cd459-5e09-42d7-aacf-f132387ed545").execute()
print("Reset successful")
