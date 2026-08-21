import logging
from typing import Dict, Any

from stage_runner import PipelineStage
from contracts import EditedStoryScript, QualityReport
from notifier import notify_script_approval

logger = logging.getLogger(__name__)

class QualityGateStage(PipelineStage):
    """
    Halts the pipeline to wait for human script approval via Telegram.
    Bypasses if the video is already approved.
    """
    name = "quality_gate"
    output_type = "QualityReport"

    def execute(self, inputs: Dict[str, Any]) -> QualityReport:
        story = inputs.get("story_script")
        if not story:
            raise ValueError("Missing story_script in QualityGateStage")

        # Handle both dict (from cache) and object (from fresh generation)
        word_count = story.get("total_word_count") if isinstance(story, dict) else story.total_word_count
        title = story.get("title_variant") if isinstance(story, dict) else story.title_variant
        beats = story.get("beats") if isinstance(story, dict) else story.beats
        story_id = story.get("artifact_id") if isinstance(story, dict) else story.artifact_id

        # 1. Check if it's already approved
        res = self.sb.table("videos").select("status").eq("id", self.video_id).execute()
        if not res.data:
            raise ValueError(f"Video {self.video_id} not found in DB.")
            
        status = res.data[0].get("status")
        
        # If it's already past the script approval stage, just pass it through
        if status in ["processing", "completed", "published", "awaiting_preview_approval", "awaiting_publish_approval", "approved"]:
            logger.info(f"[{self.name}] Video {self.video_id} is already in state '{status}'. Passing through.")
            return QualityReport(
                artifact_id=f"qr-{self.video_id}",
                video_id=self.video_id,
                is_approved=True,
                findings=[],
                parent_artifact_ids=[story_id]
            )
            
        # 2. Hard Blockers Check (Example: Script too short)
        if word_count < 100:
            logger.error(f"[{self.name}] Hard blocker: Script is only {word_count} words.")
            raise ValueError("Script is too short.")
            
        # 3. Halt and Notify
        if status != "awaiting_script_approval":
            logger.info(f"[{self.name}] Requesting human approval for {self.video_id}")
            # Update DB
            self.sb.table("videos").update({"status": "awaiting_script_approval"}).eq("id", self.video_id).execute()
            
            # Get hook text for preview
            # Handle both dicts and objects for beats
            hook_beats = [b.get("narration") if isinstance(b, dict) else b.narration for b in beats[:3]]
            hook_text = " ".join(hook_beats)
            
            # Send Telegram notification
            notify_script_approval(
                video_id=self.video_id,
                title=title,
                hook_text=hook_text,
                total_words=word_count,
                webhook_url=""
            )
            
        raise Exception("HALT: Awaiting Human Approval. Pipeline will resume when approved.")
