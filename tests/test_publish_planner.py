import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from publish_planner import PublishPackageStage, PublishMetadataPlan
from contracts import PromiseContract, EditedStoryScript, StoryBeat, PublishPackage

def test_publish_planner_mock_mode():
    # Enable mock mode
    os.environ["MOCK_EXTERNAL_APIS"] = "true"
    
    sb = MagicMock()
    stage = PublishPackageStage(sb, "vid_123")
    
    # Mock LLM response
    mock_metadata = PublishMetadataPlan(
        title="Epic Test Video",
        description="This is an epic test.",
        tags=["test", "epic"],
        thumbnail_concept="A majestic test runner."
    )
    
    stage.generate_structured = MagicMock(return_value=mock_metadata)
    
    promise = PromiseContract(
        artifact_id="art_1",
        video_id="vid_123",
        target_title="Original Title",
        topic_premise="Testing",
        primary_claim="Code works",
        hook_promise="You will see code work",
        target_emotion="Joy"
    )
    
    story = EditedStoryScript(
        artifact_id="art_2",
        video_id="vid_123",
        title_variant="Final Title",
        beats=[],
        total_word_count=500
    )
    
    result = stage.execute({"promise_contract": promise, "story_script": story})
    
    assert isinstance(result, PublishPackage)
    assert result.title == "Epic Test Video"
    assert result.description == "This is an epic test."
    assert result.tags == ["test", "epic"]
    # Verify mock thumbnail was injected
    assert len(result.thumbnail_urls) == 1
    assert "unsplash" in result.thumbnail_urls[0]
    
    # Clean up mock environment variable
    del os.environ["MOCK_EXTERNAL_APIS"]
