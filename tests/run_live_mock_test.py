import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from run_v2 import run_v2_story_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Force Mock APIs so we don't spend ElevenLabs or Fal.ai credits
os.environ["MOCK_EXTERNAL_APIS"] = "true"

def run_test():
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Insert a dummy video
    logger.info("Inserting dummy video project for testing...")
    res = sb.table("videos").insert({
        "target_title": "The Rise and Fall of Blockbuster Video",
        "topic_premise": "How the dominant video rental chain failed to adapt to the digital age and was crushed by Netflix."
    }).execute()
    
    if not res.data:
        logger.error("Failed to insert dummy video.")
        return
        
    video_id = res.data[0]["id"]
    logger.info(f"Created dummy video with ID: {video_id}")
    
    # Run the V2 pipeline
    logger.info("Running V2 Pipeline in Mock Mode...")
    run_v2_story_pipeline(video_id)
    
    # Verify outputs
    artifacts = sb.table("artifacts").select("artifact_type").eq("video_id", video_id).execute()
    types = [a["artifact_type"] for a in artifacts.data]
    logger.info(f"Generated artifacts in DB: {types}")
    
if __name__ == "__main__":
    run_test()
