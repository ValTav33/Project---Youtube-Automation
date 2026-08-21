#!/usr/bin/env python3
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client
import os

from story_engines import (
    PromiseStage,
    ResearchStage,
    HookStage,
    StoryStage,
    RetentionEditorStage
)
from scene_director import IntentStage, ShotStage, ManifestStage
from voice_compiler import VoiceStage
from asset_planner import AssetStage
from quality_gate import QualityGateStage
from publish_planner import PublishPackageStage
from publisher import send_telegram_review_gate
from analytics_extractor import AnalyticsFeatureVectorStage

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def run_v2_story_pipeline(video_id: str):
    logger.info(f"Starting V2 Story Pipeline for video {video_id}")
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase credentials missing.")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # 1. Fetch Video Context
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data
    if not video:
        logger.error(f"Video {video_id} not found.")
        return
        
    logger.info(f"Target Title: {video.get('target_title')}")
    
    # 2. Initialize Stages
    promise_stage = PromiseStage(sb, video_id)
    research_stage = ResearchStage(sb, video_id)
    hook_stage = HookStage(sb, video_id)
    story_stage = StoryStage(sb, video_id)
    editor_stage = RetentionEditorStage(sb, video_id)
    quality_gate = QualityGateStage(sb, video_id)
    
    intent_stage = IntentStage(sb, video_id)
    voice_stage = VoiceStage(sb, video_id)
    shot_stage = ShotStage(sb, video_id)
    asset_stage = AssetStage(sb, video_id)
    manifest_stage = ManifestStage(sb, video_id)
    
    publish_stage = PublishPackageStage(sb, video_id)
    analytics_stage = AnalyticsFeatureVectorStage(sb, video_id)
    
    # 3. Execute Stages sequentially
    try:
        promise = promise_stage.run({
            "target_title": video.get("target_title"), 
            "topic_premise": video.get("topic_premise")
        })
        
        research = research_stage.run({"promise_contract": promise})
        
        hook = hook_stage.run({
            "promise_contract": promise,
            "research_packet": research
        })
        
        story = story_stage.run({
            "promise_contract": promise,
            "research_packet": research,
            "hook_script": hook
        })
        
        edited_story = editor_stage.run({
            "story_script": story
        })
        
        # --- QUALITY GATE ---
        # Will block and throw an exception if status is not already approved
        gate_passed = quality_gate.run({
            "story_script": edited_story
        })
        
        # --- SCENE DIRECTOR & COMPILER ---
        intent = intent_stage.run({
            "story_script": edited_story
        })
        
        timing = voice_stage.run({
            "story_script": edited_story
        })
        
        shot_plan = shot_stage.run({
            "scene_intent": intent,
            "timing_map": timing,
            "story_script": edited_story
        })
        
        asset_manifest = asset_stage.run({
            "scene_intent": intent,
            "shot_plan": shot_plan
        })
        
        manifest = manifest_stage.run({
            "story_script": edited_story,
            "timing_map": timing,
            "shot_plan": shot_plan,
            "asset_manifest": asset_manifest
        })
        
        # --- PUBLISH PACKAGE ---
        publish_package = publish_stage.run({
            "promise_contract": promise,
            "story_script": edited_story
        })
        
        # --- ANALYTICS EXTRACTOR ---
        feature_vector = analytics_stage.run({
            "promise_contract": promise,
            "story_script": edited_story,
            "shot_plan": shot_plan,
            "publish_package": publish_package
        })
        
        logger.info(f"✅ V2 Pipeline completed generation successfully for {video_id}")
        
        # --- PUBLISH GATE ---
        status = video.get("status")
        if status not in ["awaiting_publish_approval", "publishing", "published"]:
            logger.info(f"Triggering Publish Review Gate for {video_id}...")
            send_telegram_review_gate(video_id)
            logger.info("Pipeline halting to await manual Publish approval.")
            
    except Exception as e:
        logger.error(f"❌ V2 Pipeline halted/failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_v2_story_pipeline(sys.argv[1])
    else:
        print("Usage: python src/run_v2.py <video_id>")
