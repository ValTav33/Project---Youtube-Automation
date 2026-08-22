#!/usr/bin/env python3
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client
import os

from story_engines import (
    ResearchAgentStage,
    AngleSelectorStage,
    MarketingStrategistStage,
    ThumbnailPromptCreatorStage,
    StoryArchitectStage,
    ScriptWriterStage,
    RetentionCriticStage,
    ScriptRewriterStage,
    QualityEvaluatorStage
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
    logger.info(f"Starting V2 Story Pipeline (Multi-Agent) for video {video_id}")
    
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
    research_stage = ResearchAgentStage(sb, video_id)
    angle_stage = AngleSelectorStage(sb, video_id)
    strategist_stage = MarketingStrategistStage(sb, video_id)
    prompt_creator_stage = ThumbnailPromptCreatorStage(sb, video_id)
    architect_stage = StoryArchitectStage(sb, video_id)
    writer_stage = ScriptWriterStage(sb, video_id)
    critic_stage = RetentionCriticStage(sb, video_id)
    rewriter_stage = ScriptRewriterStage(sb, video_id)
    
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
        research = research_stage.run({
            "target_title": video.get("target_title")
        })
        
        angle = angle_stage.run({
            "target_title": video.get("target_title"),
            "research_packet": research
        })
        
        marketing_strategy = strategist_stage.run({
            "angle_strategy": angle
        })
        
        thumbnail_prompt = prompt_creator_stage.run({
            "marketing_strategy": marketing_strategy
        })
        
        # --- PHASE 4: AUTO-REGENERATION LOOP ---
        quality_report = None
        max_retries = 2
        for attempt in range(max_retries + 1):
            if attempt == 0:
                beat_plan = architect_stage.run({
                    "marketing_strategy": marketing_strategy,
                    "research_packet": research
                })
                
                story = writer_stage.run({
                    "story_beat_plan": beat_plan,
                    "research_packet": research,
                    "marketing_strategy": marketing_strategy
                })
                
                critic_review = critic_stage.run({
                    "story_script": story
                })
                
                edited_story = rewriter_stage.run({
                    "story_script": story,
                    "critic_review": critic_review
                })
            else:
                logger.info(f"Auto-Regeneration Attempt {attempt} for video {video_id}")
                # The rewriter uses the strict quality report as feedback
                edited_story = rewriter_stage.run({
                    "story_script": edited_story,
                    "critic_review": quality_report
                })

            quality_evaluator = QualityEvaluatorStage(video_id, session_id)
            quality_report = quality_evaluator.run({
                "story_script": edited_story
            })
            
            if quality_report.is_approved:
                logger.info(f"Quality Approved! Score: {quality_report.overall_score}/10")
                break
            else:
                logger.warning(f"Quality Rejected. Score: {quality_report.overall_score}/10. Flaws: {quality_report.critical_flaws}")
                if attempt == max_retries:
                    logger.error("Max retries reached. Proceeding with best effort.")
        
        # --- QUALITY GATE ---
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
            "marketing_strategy": marketing_strategy,
            "thumbnail_prompt_plan": thumbnail_prompt,
            "story_script": edited_story
        })
        
        # --- ANALYTICS EXTRACTOR ---
        # Note: we pass angle instead of promise for analytics in V2.1
        feature_vector = analytics_stage.run({
            "promise_contract": angle, # Retrofit for Analytics
            "story_script": edited_story,
            "shot_plan": shot_plan,
            "publish_package": publish_package
        })
        
        logger.info(f"✅ V2 Multi-Agent Pipeline completed generation successfully for {video_id}")
        
        # --- PUBLISH GATE ---
        status = video.get("status")
        if status not in ["awaiting_publish_approval", "publishing", "published"]:
            logger.info(f"Triggering Publish Review Gate for {video_id}...")
            send_telegram_review_gate(video_id)
            logger.info("Pipeline halting to await manual Publish approval.")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        # Update video status to error
        # sb.table("videos").update({"status": "error"}).eq("id", video_id).execute()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        vid_id = sys.argv[1]
        run_v2_story_pipeline(vid_id)
    else:
        logger.error("Usage: python src/run_v2.py <video_id>")
