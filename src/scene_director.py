import logging
from typing import Dict, Any
from pydantic import BaseModel

from stage_runner import PipelineStage
from story_engines import BaseOpenAIStage
from contracts import (
    EditedStoryScript,
    SceneIntentPlan,
    TimingMap,
    ShotPlan,
    Shot
)

logger = logging.getLogger(__name__)

class IntentStage(BaseOpenAIStage):
    """
    Translates narrative beats into high-level visual directions without exact timing.
    """
    name = "scene_intent_generation"
    output_type = "SceneIntentPlan"

    def execute(self, inputs: Dict[str, Any]) -> SceneIntentPlan:
        story_raw = inputs.get("story_script")
        if not story_raw:
            raise ValueError("Missing story_script")
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw

            
        system = (
            "You are a documentary visual director. For each beat in the script, "
            "determine the visual subject, motion intensity, and an exact b-roll search query. "
            "Keep the b-roll query optimized for stock video (e.g. 'cargo ship ocean storm')."
        )
        
        script_text = "\\n".join([f"[{b.beat_id}] {b.narration}" for b in story.beats])
        user = f"Generate a Scene Intent Plan for this script:\n\n{script_text}"
        
        parsed = self.generate_structured(system, user, SceneIntentPlan)
        parsed.artifact_id = f"intent-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [story.artifact_id]
        
        # Ensure a scene ID is assigned to each intent
        for i, scene in enumerate(parsed.scenes):
            scene.scene_id = f"scene_{i+1}"
            
        return parsed


class ShotStage(PipelineStage):
    """
    Compiles exact shot timing by mapping visual scenes to audio word timestamps.
    Deterministic stage (does not use AI).
    """
    name = "shot_compilation"
    output_type = "ShotPlan"

    def execute(self, inputs: Dict[str, Any]) -> ShotPlan:
        intent_raw = inputs.get("scene_intent")
        timing_raw = inputs.get("timing_map")
        
        if not intent_raw or not timing_raw:
            raise ValueError("Missing scene_intent or timing_map")
            
        intent = SceneIntentPlan.model_validate(intent_raw) if isinstance(intent_raw, dict) else intent_raw
        timing = TimingMap.model_validate(timing_raw) if isinstance(timing_raw, dict) else timing_raw
            
        fps = 30
        shots = []
        
        # We need to map each scene intent to a time range.
        # Since ElevenLabs doesn't output beat boundaries directly, we assume sequential alignment.
        # The total words in the script should match the words in TimingMap, but realistically TTS may drop punctuation or combine words.
        # For a robust MVP compiler, we will divide the total audio duration proportionally based on word count per scene intent, 
        # or just align by tracking narration word count.
        
        total_audio_words = len(timing.words)
        total_audio_duration = timing.total_duration_seconds
        total_frames = int(total_audio_duration * fps)
        
        # Simple proportional mapping:
        current_frame = 0
        total_beat_words = sum(len(scene.broll_search_query.split()) for scene in intent.scenes) # this is wrong, we need beat word count
        # Wait, SceneIntentPlan doesn't store word count. We need the original beats!
        story_raw = inputs.get("story_script")
        if not story_raw:
            raise ValueError("Missing story_script required for shot alignment")
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw
            
        beat_durations = {}
        total_script_words = sum(b.word_count for b in story.beats)
        
        # Map beats to frames
        current_f = 0
        for beat in story.beats:
            ratio = beat.word_count / (total_script_words or 1)
            frames = int(ratio * total_frames)
            beat_durations[beat.beat_id] = frames
        
        # Adjust last beat to consume remaining frames exactly
        assigned_frames = sum(beat_durations.values())
        if story.beats:
            beat_durations[story.beats[-1].beat_id] += (total_frames - assigned_frames)
            
        # Count scenes per beat
        from collections import Counter
        beat_scene_counts = Counter(scene.beat_id for scene in intent.scenes)
        
        beat_allocated_frames = {b: 0 for b in beat_scene_counts}
        beat_scene_index = {b: 0 for b in beat_scene_counts}
        
        # Map scenes to shots
        current_frame = 0
        for idx, scene in enumerate(intent.scenes):
            beat_id = scene.beat_id
            total_beat_frames = beat_durations.get(beat_id, fps * 3)
            num_scenes = beat_scene_counts[beat_id]
            
            base_duration = total_beat_frames // num_scenes
            beat_scene_index[beat_id] += 1
            
            if beat_scene_index[beat_id] == num_scenes:
                duration_frames = total_beat_frames - beat_allocated_frames[beat_id]
            else:
                duration_frames = base_duration
                
            beat_allocated_frames[beat_id] += duration_frames
            
            shot = Shot(
                shot_id=f"shot_{idx+1}",
                scene_id=scene.scene_id,
                start_frame=current_frame,
                end_frame=current_frame + duration_frames - 1,
                duration_frames=duration_frames
            )
            shots.append(shot)
            current_frame += duration_frames
            
        plan = ShotPlan(
            artifact_id=f"shotplan-{self.video_id}",
            video_id=self.video_id,
            shots=shots,
            fps=fps
        )
        plan.parent_artifact_ids = [intent.artifact_id, timing.artifact_id, story.artifact_id]
        return plan

class ManifestStage(PipelineStage):
    """
    Compiles all generated artifacts into the final renderer manifest JSON.
    """
    name = "manifest_compilation"
    output_type = "RendererManifest"

    def execute(self, inputs: Dict[str, Any]) -> BaseModel:
        # Since this stage outputs a generic JSON that Remotion consumes, 
        # we will use a dynamic Pydantic model or just return a simple wrapper.
        from pydantic import BaseModel
        class RendererManifest(BaseModel):
            artifact_type: str = "RendererManifest"
            artifact_id: str
            video_id: str
            parent_artifact_ids: list[str] = []
            payload: Dict[str, Any]
            
        story_raw = inputs.get("story_script")
        timing_raw = inputs.get("timing_map")
        shot_plan_raw = inputs.get("shot_plan")
        manifest_raw = inputs.get("asset_manifest")
        
        from contracts import AssetManifest
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw
        timing = TimingMap.model_validate(timing_raw) if isinstance(timing_raw, dict) else timing_raw
        shot_plan = ShotPlan.model_validate(shot_plan_raw) if isinstance(shot_plan_raw, dict) else shot_plan_raw
        manifest = AssetManifest.model_validate(manifest_raw) if isinstance(manifest_raw, dict) else manifest_raw
        
        # Build the final remotion props shape
        remotion_scenes = []
        asset_map = {a.scene_id: a for a in manifest.assets}
        
        for shot in shot_plan.shots:
            asset = asset_map.get(shot.scene_id)
            # Find narration from story based on time or just pass the whole words array
            # We already have word timestamps in timing map
            remotion_scenes.append({
                "scene_id": shot.scene_id,
                "shot_id": shot.shot_id,
                "durationInFrames": shot.duration_frames,
                "asset_type": asset.asset_type if asset else "image",
                "asset_url": asset.asset_url if asset else "",
                "start_frame": shot.start_frame,
                "end_frame": shot.end_frame
            })
            
        final_props = {
            "scenes": remotion_scenes,
            "words": [w.model_dump() for w in timing.words],
            "audioUrl": timing.audio_url,
            "bgMusicUrl": "",
            "bgMusicVolume": 0.12,
            "fps": shot_plan.fps
        }
        
        return RendererManifest(
            artifact_id=f"manifest-{self.video_id}",
            video_id=self.video_id,
            parent_artifact_ids=[story.artifact_id, timing.artifact_id, shot_plan.artifact_id, manifest.artifact_id],
            payload=final_props
        )
