import logging
from typing import Dict, Any

from stage_runner import PipelineStage
from contracts import EditedStoryScript
from notifier import notify_script_approval

logger = logging.getLogger(__name__)

class QualityGateStage(PipelineStage):
    """
    Checks the current script against basic rules and halts execution,
    sending a Telegram notification to the human approver.
    """
    name = "quality_gate"
    output_type = "EditedStoryScript" # It passes through the script if approved

    def execute(self, inputs: Dict[str, Any]) -> EditedStoryScript:
        story: EditedStoryScript = inputs.get("story_script")
        if not story:
            raise ValueError("Missing story_script in QualityGateStage")

        # 1. Check if it's already approved
        res = self.sb.table("videos").select("status").eq("id", self.video_id).execute()
        if not res.data:
            raise ValueError(f"Video {self.video_id} not found in DB.")
            
        status = res.data[0].get("status")
        
        # If it's already past the script approval stage, just pass it through
        if status in ["processing", "completed", "published", "awaiting_preview_approval", "awaiting_publish_approval", "approved"]:
            logger.info(f"[{self.name}] Video {self.video_id} is already in state '{status}'. Passing through.")
            return story
            
        # 2. Hard Blockers Check (Example: Script too short)
        if story.total_word_count < 100:
            logger.error(f"[{self.name}] Hard blocker: Script is only {story.total_word_count} words.")
            raise ValueError("Script is too short.")
            
        # 3. Halt and Notify
        if status != "awaiting_script_approval":
            logger.info(f"[{self.name}] Requesting human approval for {self.video_id}")
            # Update DB
            self.sb.table("videos").update({"status": "awaiting_script_approval"}).eq("id", self.video_id).execute()
            
            # Get hook text for preview
            hook_beats = [b.narration for b in story.beats[:3]]
            hook_text = " ".join(hook_beats)
            
            # Send Telegram notification
            notify_script_approval(
                video_id=self.video_id,
                title=story.title_variant,
                hook_text=hook_text,
                total_words=story.total_word_count,
                webhook_url=""
            )
            
        raise Exception("HALT: Awaiting Human Approval. Pipeline will resume when approved.")
