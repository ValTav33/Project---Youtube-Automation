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

    def process_generation_phase(self, video_id: str) -> bool:
        """
        Placeholder for the actual AI generation process (Phase 3 & 4).
        Will return artifacts.
        """
        logger.info(f"Starting generation phase for {video_id}...")
        
        # This would call the Strategy, Story, and Visual agents sequentially
        # and persist their Pydantic artifacts to the database.
        
        return True
