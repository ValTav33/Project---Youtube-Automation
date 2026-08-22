import os
import logging
from typing import Dict, Any

from stage_runner import PipelineStage
from contracts import EditedStoryScript, TimingMap, WordTimestamp
from audio_generator import generate_speech_with_timestamps

logger = logging.getLogger(__name__)

class VoiceStage(PipelineStage):
    """
    Generates narration audio from the script and extracts word-level timestamps.
    """
    name = "voice_generation"
    output_type = "TimingMap"

    def execute(self, inputs: Dict[str, Any]) -> TimingMap:
        story_raw = inputs.get("story_script")
        if not story_raw:
            raise ValueError("Missing story_script input")
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw
            
        full_narration = " ".join([b.narration for b in story.beats])
        logger.info(f"[{self.name}] Generating speech for {len(full_narration.split())} words...")
        
        # Check if we should run in mock mode
        if os.getenv("MOCK_EXTERNAL_APIS") == "true":
            logger.info(f"[{self.name}] MOCK MODE ENABLED: Bypassing ElevenLabs.")
            duration = len(full_narration.split()) * 0.4
            words = [
                WordTimestamp(word=w, start=i*0.4, end=(i*0.4)+0.3) 
                for i, w in enumerate(full_narration.split())
            ]
            audio_url = "https://example.com/mock_audio.mp3"
        else:
            # Call the actual ElevenLabs function
            audio_bytes, raw_words, duration = generate_speech_with_timestamps(full_narration)
            
            # Upload to Supabase
            file_path = f"{self.video_id}.mp3"
            self.sb.storage.from_("audio").upload(
                path=file_path,
                file=audio_bytes,
                file_options={"content-type": "audio/mpeg", "upsert": "true"}
            )
            public_url = self.sb.storage.from_("audio").get_public_url(file_path)
            audio_url = public_url if isinstance(public_url, str) else public_url.get("publicUrl", "")
            
            # Map raw dicts to Pydantic models
            words = [WordTimestamp(**w) for w in raw_words]
            
        timing_map = TimingMap(
            artifact_id=f"timing-{self.video_id}",
            video_id=self.video_id,
            words=words,
            total_duration_seconds=duration,
            audio_url=audio_url
        )
        timing_map.parent_artifact_ids = [story.artifact_id]
        
        return timing_map
