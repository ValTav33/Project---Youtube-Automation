import logging
import os
import time
from typing import Optional, Dict, Any, Literal
from dotenv import load_dotenv

from config import validate_config

# Import V3 schemas
from contracts_v3 import (
    VideoBrief,
    VerifiedResearchPacket,
    StoryBlueprint,
    VisualBriefPlan,
    ProductionManifest
)

load_dotenv()
validate_config()

logger = logging.getLogger(__name__)

V3LifecycleState = Literal[
    "discovered", 
    "approved", 
    "generating", 
    "awaiting_preview_approval", 
    "rendering", 
    "awaiting_publish_approval", 
    "publishing", 
    "published",
    "failed"
]

class V3Orchestrator:
    """
    The central state machine for the V3 video production pipeline.
    It enforces valid state transitions and guarantees that stages return 
    artifacts rather than mutating global database state directly.
    """
    def __init__(self, db_client=None):
        self.db = db_client

    def transition_state(self, video_id: str, current_state: V3LifecycleState, next_state: V3LifecycleState, 
                         payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validates and executes a state transition.
        In a real app, this would write to Supabase `videos` table.
        """
        valid_transitions = {
            "discovered": ["approved", "failed"],
            "approved": ["generating", "failed"],
            "generating": ["awaiting_preview_approval", "failed"],
            "awaiting_preview_approval": ["rendering", "failed", "generating"], # Can go back for repair
            "rendering": ["awaiting_publish_approval", "failed"],
            "awaiting_publish_approval": ["publishing", "failed", "awaiting_preview_approval"],
            "publishing": ["published", "failed"],
            "failed": ["approved", "generating", "rendering", "publishing"] # Resume points
        }

        if next_state not in valid_transitions.get(current_state, []):
            logger.error(f"Invalid transition from {current_state} to {next_state} for video {video_id}")
            return False

        logger.info(f"Transitioning video {video_id} from {current_state} -> {next_state}")
        
        # Here you would typically perform the DB update
        if self.db:
            try:
                update_data = {"status": next_state, "pipeline_version": 3, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
                if payload:
                    update_data["v3_payload"] = payload
                    
                self.db.table("videos").update(update_data).eq("id", video_id).execute()
            except Exception as e:
                logger.error(f"Failed to update state in DB: {e}")
                return False

        return True

    def process_generation_phase(self, video_id: str, topic: str) -> Optional[ProductionManifest]:
        """
        Executes the AI pipeline (Strategy -> Research -> Story -> Visuals -> Compile).
        Returns the final ProductionManifest on success, or None on failure.
        """
        logger.info(f"Starting V3 generation phase for {video_id} (topic: {topic})...")
        
        try:
            # 1. Strategy
            from agents_v3 import (
                StrategyAgent, MockResearchAgent, StoryAgent, VisualDirectorAgent,
                MockAssetCuratorAgent, MockAudioDirectorAgent
            )
            from compiler_v3 import ManifestCompiler
            
            self.transition_state(video_id, "approved", "generating")
            
            strategy_agent = StrategyAgent()
            brief = strategy_agent.generate_brief(video_id, topic)
            logger.info(f"Generated brief: {brief.artifact_id}")
            
            # 2. Research
            research_agent = MockResearchAgent()
            research = research_agent.run_research(video_id, brief)
            logger.info(f"Generated research: {research.artifact_id}")
            
            # 3. Story
            story_agent = StoryAgent()
            story = story_agent.draft_story(video_id, brief, research)
            logger.info(f"Generated story: {story.artifact_id}")
            
            # 4. Visuals
            visual_agent = VisualDirectorAgent()
            visuals = visual_agent.assign_visuals(video_id, story)
            logger.info(f"Generated visual plan: {visuals.artifact_id}")
            
            # 5. Assets
            asset_agent = MockAssetCuratorAgent()
            assets = asset_agent.resolve_assets(video_id, visuals)
            logger.info(f"Generated asset manifest: {assets.artifact_id}")
            
            # 6. Audio
            audio_agent = MockAudioDirectorAgent()
            audio = audio_agent.plan_audio(video_id, story, visuals)
            logger.info(f"Generated audio plan: {audio.artifact_id}")
            
            # 7. Compile Manifest
            compiler = ManifestCompiler()
            manifest = compiler.compile(video_id, story, visuals, assets, audio)
            logger.info(f"Compiled manifest: {manifest.artifact_id} with {manifest.total_frames} frames")
            
            # Success - wait for preview approval
            self.transition_state(video_id, "generating", "awaiting_preview_approval")
            return manifest
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            self.transition_state(video_id, "generating", "failed")
            return None
