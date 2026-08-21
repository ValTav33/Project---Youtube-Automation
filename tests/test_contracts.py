import pytest
from pydantic import ValidationError
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from contracts import PromiseContract, StoryScript

def test_promise_contract_validation():
    # Valid contract
    contract = PromiseContract(
        artifact_id="art-123",
        video_id="vid-123",
        target_title="My Test Video",
        topic_premise="This is a test premise.",
        primary_claim="This video will prove X.",
        hook_promise="In 30 seconds, you will see Y.",
        target_emotion="curiosity"
    )
    
    assert contract.artifact_type == "PromiseContract"
    assert contract.schema_version == "1.0.0"
    
    # Missing required field
    with pytest.raises(ValidationError):
        PromiseContract(
            artifact_id="art-123",
            video_id="vid-123",
            target_title="My Test Video",
            # missing topic_premise
            primary_claim="Claim",
            hook_promise="Hook",
            target_emotion="emotion"
        )

def test_story_script_validation():
    script = StoryScript(
        artifact_id="art-456",
        video_id="vid-123",
        title_variant="Title 1",
        total_word_count=45,
        beats=[
            {
                "beat_id": "b1",
                "narration": "Hello world.",
                "word_count": 2,
                "intent": "Hook"
            }
        ]
    )
    assert len(script.beats) == 1
    assert script.beats[0].narration == "Hello world."
