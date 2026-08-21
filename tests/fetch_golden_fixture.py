#!/usr/bin/env python3
import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def fetch_golden_fixture():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase credentials not found in env.")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Try to find a published or rendered video
    res = sb.table("videos").select("*").in_("status", ["published", "rendered"]).order("created_at", desc=True).limit(1).execute()
    
    data = res.data
    if not data:
        logger.warning("No published or rendered video found to use as a golden fixture. Fetching any completed script instead.")
        res = sb.table("videos").select("*").not_.is_("script_payload", "null").order("created_at", desc=True).limit(1).execute()
        data = res.data

    if not data:
        logger.error("No valid video records found in the database.")
        return

    video = data[0]
    
    os.makedirs("tests/fixtures", exist_ok=True)
    out_path = "tests/fixtures/golden_video.json"
    
    with open(out_path, "w") as f:
        json.dump(video, f, indent=2)
        
    logger.info(f"Successfully saved video ID {video['id']} as golden fixture to {out_path}.")

if __name__ == "__main__":
    fetch_golden_fixture()
