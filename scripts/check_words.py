import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
res = sb.table("artifacts").select("payload").eq("video_id", "483cd459-5e09-42d7-aacf-f132387ed545").eq("artifact_type", "AudioTrack").order("revision", desc=True).limit(1).execute()
words = res.data[0]["payload"]["word_alignments"]
print(f"Total words: {len(words)}")
if words:
    print(f"First word: {words[0]}")
    print(f"Last word: {words[-1]}")
