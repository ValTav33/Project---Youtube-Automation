import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
for s in ["discovered", "approved", "scripting", "voiceover", "rendering", "publishing", "published", "failed"]:
    try:
        sb.table("videos").update({"status": s}).eq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"{s} IS VALID!")
    except Exception as e:
        print(f"{s} is invalid")
print("Done checking")
