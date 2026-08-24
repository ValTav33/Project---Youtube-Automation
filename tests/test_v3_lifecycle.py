import pytest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from contracts_v3 import VideoBrief
from orchestrator_v3 import V3Orchestrator

def test_pydantic_schema_validation():
    """Test that a V3 artifact correctly validates and rejects missing fields."""
    
    # Valid Brief
    brief = VideoBrief(
        artifact_id="br-1",
        video_id="vid-1",
        topic="AI Agents",
        target_duration_seconds=600,
        promise="You will learn how AI agents work.",
        audience_tension="Will agents take my job?",
        title_hypothesis="The Truth About AI Agents",
        thumbnail_hypothesis="Robot at a desk",
        creative_bible_version="cb-1"
    )
    
    assert brief.topic == "AI Agents"
    assert brief.artifact_type == "VideoBrief"
    
    # Missing required field
    with pytest.raises(ValueError):
        VideoBrief(
            artifact_id="br-2",
            video_id="vid-1",
            topic="Bad Topic",
            # target_duration_seconds missing
            promise="Bad promise",
            audience_tension="Tension",
            title_hypothesis="Title",
            thumbnail_hypothesis="Thumb",
            creative_bible_version="cb-1"
        )

def test_v3_lifecycle_transitions():
    """Test that the orchestrator enforces the correct V3 lifecycle."""
    orchestrator = V3Orchestrator(db_client=None)  # DB mocked as None
    
    video_id = "test-vid-1"
    
    # Valid flow
    assert orchestrator.transition_state(video_id, "discovered", "approved") == True
    assert orchestrator.transition_state(video_id, "approved", "generating") == True
    assert orchestrator.transition_state(video_id, "generating", "awaiting_preview_approval") == True
    assert orchestrator.transition_state(video_id, "awaiting_preview_approval", "rendering") == True
    
    # Invalid jump
    assert orchestrator.transition_state(video_id, "rendering", "published") == False # Cannot skip awaiting_publish_approval
    
    # Rejection flow (repair)
    assert orchestrator.transition_state(video_id, "awaiting_preview_approval", "generating") == True
    
    # Failure & Resume
    assert orchestrator.transition_state(video_id, "generating", "failed") == True
    assert orchestrator.transition_state(video_id, "failed", "generating") == True
