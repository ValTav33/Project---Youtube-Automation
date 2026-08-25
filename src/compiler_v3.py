import uuid
import logging
from typing import Dict, Any

from contracts_v3 import (
    StoryBlueprint,
    VisualBriefPlan,
    AssetManifest,
    AudioPlan,
    ProductionManifest,
    RenderShot,
    AudioTrack
)

logger = logging.getLogger(__name__)

class ManifestCompiler:
    """
    Transforms AI Blueprints into deterministic Remotion JSON manifests.
    No LLM calls happen here; it is purely rule-based.
    """
    
    WORDS_PER_MINUTE = 150
    FRAMES_PER_SECOND = 30
    
    def compile(self, video_id: str, story: StoryBlueprint, visuals: VisualBriefPlan, assets: AssetManifest, audio: AudioPlan) -> ProductionManifest:
        logger.info(f"Compiling manifest for {video_id}...")
        
        shots = []
        current_frame = 0
        
        # Map beats to visuals and assets
        visual_map = {vb.beat_id: vb for vb in visuals.visual_beats}
        asset_map = {a.beat_id: a for a in assets.resolved_assets}
        
        for beat in story.beats:
            visual_beat = visual_map.get(beat.beat_id)
            if not visual_beat:
                logger.warning(f"No visual beat found for beat {beat.beat_id}, using fallback.")
                from contracts_v3 import VisualBeat, ComponentChoice
                visual_beat = VisualBeat(
                    beat_id=beat.beat_id,
                    motion_intention="fallback",
                    component_choice=ComponentChoice(
                        component_type="TypographyImpact",
                        primary_text=beat.narration_text[:30] + "..."
                    )
                )
                
            # Calculate duration based on word count
            # If actual audio duration is available, allocate proportionally to word count
            if audio.total_duration_seconds > 0:
                total_words = sum([b.word_count for b in story.beats])
                duration_seconds = max(1.0, (beat.word_count / total_words) * audio.total_duration_seconds)
            else:
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
            
            
            asset_info = asset_map.get(beat.beat_id)
            provenance = None
            if asset_info:
                provenance = {
                    "provider": asset_info.provider,
                    "license_category": asset_info.license_category
                }
            
            shot = RenderShot(
                shot_id=f"shot-{uuid.uuid4().hex[:6]}",
                start_frame=current_frame,
                duration_frames=duration_frames,
                component_type=visual_beat.component_choice.component_type,
                component_props=component_props,
                asset_url=asset_info.asset_url if asset_info else None,
                provenance=provenance
            )
            
            shots.append(shot)
            current_frame += duration_frames
            
        audio_tracks = []
        if audio.voice_track_url:
            audio_tracks.append(
                AudioTrack(
                    track_id=f"audio-{uuid.uuid4().hex[:6]}",
                    audio_type="narration",
                    asset_url=audio.voice_track_url,
                    start_frame=0,
                    duration_frames=current_frame,
                    volume=1.0
                )
            )
        
        if audio.music_track_url:
            audio_tracks.append(
                AudioTrack(
                    track_id=f"audio-{uuid.uuid4().hex[:6]}",
                    audio_type="music",
                    asset_url=audio.music_track_url,
                    start_frame=0,
                    duration_frames=current_frame,
                    volume=0.2
                )
            )
            
        manifest = ProductionManifest(
            artifact_id=f"pm-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            fps=self.FRAMES_PER_SECOND,
            width=1920,
            height=1080,
            total_frames=current_frame,
            shots=shots,
            audio_tracks=audio_tracks
        )
        
        return manifest
