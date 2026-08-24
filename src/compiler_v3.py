import uuid
import logging
from typing import Dict, Any

from contracts_v3 import (
    StoryBlueprint,
    VisualBriefPlan,
    ProductionManifest,
    RenderShot
)

logger = logging.getLogger(__name__)

class ManifestCompiler:
    """
    Transforms AI Blueprints into deterministic Remotion JSON manifests.
    No LLM calls happen here; it is purely rule-based.
    """
    
    WORDS_PER_MINUTE = 150
    FRAMES_PER_SECOND = 30
    
    def compile(self, video_id: str, story: StoryBlueprint, visuals: VisualBriefPlan) -> ProductionManifest:
        logger.info(f"Compiling manifest for {video_id}...")
        
        shots = []
        current_frame = 0
        
        # Map beats to visuals
        visual_map = {vb.beat_id: vb for vb in visuals.visual_beats}
        
        for beat in story.beats:
            visual_beat = visual_map.get(beat.beat_id)
            if not visual_beat:
                logger.warning(f"No visual beat found for beat {beat.beat_id}, skipping or using fallback.")
                continue
                
            # Calculate duration based on word count
            # wpm = 150 -> 2.5 words per second
            duration_seconds = max(3.0, beat.word_count / (self.WORDS_PER_MINUTE / 60.0))
            duration_frames = int(duration_seconds * self.FRAMES_PER_SECOND)
            
            # Map visual intention to component props
            component_props: Dict[str, Any] = {}
            
            if visual_beat.component_choice.component_type == "TypographyImpact":
                component_props["primaryText"] = visual_beat.component_choice.primary_text or beat.narration_text[:30]
            elif visual_beat.component_choice.component_type == "EvidenceCard":
                component_props["primaryText"] = visual_beat.component_choice.primary_text or "Evidence"
                component_props["secondaryText"] = visual_beat.component_choice.secondary_text or "Source"
            elif visual_beat.component_choice.component_type == "BigNumber":
                component_props["primaryText"] = visual_beat.component_choice.primary_text or "100"
                component_props["secondaryText"] = visual_beat.component_choice.secondary_text or "Metric"
            elif visual_beat.component_choice.component_type == "CinematicMedia":
                component_props["motionIntention"] = visual_beat.motion_intention
            
            shot = RenderShot(
                shot_id=f"shot-{uuid.uuid4().hex[:6]}",
                start_frame=current_frame,
                duration_frames=duration_frames,
                component_type=visual_beat.component_choice.component_type,
                component_props=component_props,
                asset_url=None # Real implementation would fetch from asset store using asset_query
            )
            
            shots.append(shot)
            current_frame += duration_frames
            
        manifest = ProductionManifest(
            artifact_id=f"pm-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            fps=self.FRAMES_PER_SECOND,
            width=1920,
            height=1080,
            total_frames=current_frame,
            shots=shots,
            audio_tracks=[] # Would generate TTS audio tracks here
        )
        
        return manifest
