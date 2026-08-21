import logging
from typing import Dict, Any
from story_engines import BaseOpenAIStage
from contracts import (
    AnalyticsFeatureVector,
    PromiseContract,
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
        promise = inputs.get("promise_contract")
        story = inputs.get("story_script")
        shots = inputs.get("shot_plan")
        publish = inputs.get("publish_package")

        if not promise or not story or not publish:
            raise ValueError("Missing inputs for AnalyticsFeatureVectorStage")

        # Handle DB dict cache
        promise_claim = promise.get("primary_claim") if isinstance(promise, dict) else promise.primary_claim
        promise_topic = promise.get("target_title") if isinstance(promise, dict) else promise.target_title
        
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
