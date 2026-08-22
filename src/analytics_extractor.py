import logging
from typing import Dict, Any
from story_engines import BaseOpenAIStage
from contracts import (
    AnalyticsFeatureVector,
    AngleStrategy,
    EditedStoryScript,
    ShotPlan,
    PublishPackage
)

logger = logging.getLogger(__name__)

class AnalyticsFeatureVectorStage(BaseOpenAIStage):
    """
    Analyzes the final generated artifacts to create a frozen snapshot 
    of the video's 'creative DNA' for later performance correlation.
    """
    name = "analytics_feature_extraction"
    output_type = "AnalyticsFeatureVector"

    def execute(self, inputs: Dict[str, Any]) -> AnalyticsFeatureVector:
        promise_raw = inputs.get("promise_contract")
        story_raw = inputs.get("story_script")
        shots_raw = inputs.get("shot_plan")
        publish_raw = inputs.get("publish_package")
        
        promise = AngleStrategy.model_validate(promise_raw) if isinstance(promise_raw, dict) else promise_raw
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw
        shots = ShotPlan.model_validate(shots_raw) if isinstance(shots_raw, dict) else shots_raw
        publish = PublishPackage.model_validate(publish_raw) if isinstance(publish_raw, dict) else publish_raw

        if not promise or not story or not publish:
            raise ValueError("Missing inputs for AnalyticsFeatureVectorStage")

        # Handle DB dict cache
        promise_claim = promise.get("core_angle") if isinstance(promise, dict) else promise.core_angle
        promise_topic = promise.get("primary_emotion") if isinstance(promise, dict) else promise.primary_emotion
        
        # Calculate some hard metrics
        total_shots = 0
        first_minute_shot_count = 0
        if shots:
            shots_list = shots.get("shots") if isinstance(shots, dict) else shots.shots
            total_shots = len(shots_list)
            # Rough estimate: first minute = first 15 scenes
            first_minute_shot_count = min(15, total_shots)

        title = publish.get("title") if isinstance(publish, dict) else publish.title

        system = (
            "You are a YouTube Analytics expert. Analyze the following video metadata and extract the creative feature vector. "
            "Categorize the topic, hook type, title strategy, and thumbnail strategy into broad, comparable buckets."
        )

        user = (
            f"Topic/Premise: {promise_topic}\n"
            f"Primary Claim: {promise_claim}\n"
            f"Final Title: {title}\n"
            f"Please generate the AnalyticsFeatureVector."
        )

        # Generate structured
        parsed = self.generate_structured(system, user, AnalyticsFeatureVector)
        
        # Inject computed metrics
        parsed.total_shots = total_shots
        parsed.first_minute_shot_count = first_minute_shot_count
        parsed.open_loop_count = 1 # Simplified for now
        parsed.hook_duration_seconds = 15.0 # Estimate
        parsed.style_profile_version = "v2_standard"

        parsed.artifact_id = f"analytics-{self.video_id}"
        parsed.video_id = self.video_id
        
        # Add parent references based on what we used
        parent_ids = []
        if isinstance(promise, dict): parent_ids.append(promise.get("artifact_id"))
        else: parent_ids.append(promise.artifact_id)
        if isinstance(publish, dict): parent_ids.append(publish.get("artifact_id"))
        else: parent_ids.append(publish.artifact_id)

        parsed.parent_artifact_ids = [pid for pid in parent_ids if pid]

        return parsed
