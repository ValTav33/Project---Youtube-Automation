import logging
import uuid
import json
from typing import Dict, Any, List
from supabase import Client
from story_engines import BaseOpenAIStage
from contracts import GlobalPerformanceFeedback

logger = logging.getLogger(__name__)

class LearningEngineStage(BaseOpenAIStage):
    """
    Analyzes historical AnalyticsFeatureVectors and mock performance metrics 
    to extract actionable feedback (GlobalPerformanceFeedback) for future videos.
    """
    name = "learning_engine"
    output_type = "GlobalPerformanceFeedback"
    
    def __init__(self, sb: Client):
        # The Learning Engine doesn't operate on a single video_id, 
        # but we use a dummy one to satisfy BaseOpenAIStage for now.
        super().__init__(sb, "00000000-0000-0000-0000-000000000000")

    def execute(self, inputs: Dict[str, Any]) -> GlobalPerformanceFeedback:
        # 1. Fetch recent AnalyticsFeatureVectors from Supabase
        res = self.sb.table("artifacts").select("payload").eq("artifact_type", "AnalyticsFeatureVector").order("created_at", desc=True).limit(10).execute()
        
        feature_vectors = []
        if res.data:
            for row in res.data:
                feature_vectors.append(row["payload"])
                
        if not feature_vectors:
            logger.warning("No AnalyticsFeatureVectors found. Returning default feedback.")
            return GlobalPerformanceFeedback(
                artifact_id=f"learning-{int(uuid.uuid4().time)}",
                hook_learnings=["Data insufficient: Start with high energy."],
                pacing_learnings=["Data insufficient: Keep sentences short."],
                thumbnail_learnings=["Data insufficient: Use high contrast."],
                current_channel_meta="We are still gathering data. Focus on clarity and high retention basics."
            )
            
        # 2. Simulate pulling YouTube API Metrics (CTR, AVD) for these videos
        # In the future, this will be a real API call to YouTube Analytics joining on video_id.
        mock_performance_data = []
        for fv in feature_vectors:
            # We mock that videos with more than 15 shots in the first minute performed better
            shot_count = fv.get("first_minute_shot_count", 0)
            avd_percentage = 40.0 + (shot_count * 1.5) # Mock correlation
            
            mock_performance_data.append({
                "video_id": fv.get("video_id"),
                "topic": fv.get("topic_category"),
                "hook_type": fv.get("hook_classification"),
                "first_minute_shots": shot_count,
                "simulated_retention_rate": min(avd_percentage, 75.0), # cap at 75%
                "simulated_ctr": 5.0 + (len(fv.get("thumbnail_style", "")) % 5)
            })

        # 3. Ask GPT to analyze the mock data and produce GlobalPerformanceFeedback
        system = (
            "You are a YouTube Algorithm and Analytics Expert. "
            "Analyze the following performance metrics from our recent videos. "
            "Extract concrete, actionable rules about what works and what doesn't for this channel. "
            "Formulate these as strict directives for the creative agents (writers, strategists) to follow in future videos."
        )
        
        user = f"Recent Video Analytics Data:\n{json.dumps(mock_performance_data, indent=2)}\n\nGenerate the GlobalPerformanceFeedback based on these patterns."
        
        parsed = self.generate_structured(system, user, GlobalPerformanceFeedback)
        parsed.artifact_id = f"learning-{int(uuid.uuid4().time)}"
        
        logger.info(f"[learning_engine] Generated new channel meta: {parsed.current_channel_meta}")
        return parsed
