import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from quality_gate import QualityGateStage
from contracts import EditedStoryScript, StoryBeat

@patch("quality_gate.notify_script_approval")
def test_quality_gate_blocks_on_first_run(mock_notify):
    sb = MagicMock()
    # Mock DB returns 'pending_generation'
    sb.table().select().eq().execute.return_value.data = [{"status": "pending_generation"}]

    
    stage = QualityGateStage(sb, "vid_123")
    
    story = EditedStoryScript(
        artifact_id="art_1",
        video_id="vid_123",
        title_variant="Test Video",
        total_word_count=500,
        beats=[StoryBeat(beat_id="1", word_count=4, intent="hook", narration="This is a test beat.")],
        assets=[]
    )
    
    # Expect it to halt
    with pytest.raises(Exception, match="HALT: Awaiting Human Approval"):
        stage.execute({"story_script": story})
        
    # Check that DB was updated to awaiting_script_approval
    sb.table().update.assert_called_with({"status": "awaiting_script_approval"})
    # Verify the mock was called
    mock_notify.assert_called_once()

def test_quality_gate_passes_if_approved():
    sb = MagicMock()
    # Mock DB returns 'approved'
    sb.table().select().eq().execute.return_value.data = [{"status": "approved"}]
    
    stage = QualityGateStage(sb, "vid_123")
    
    story = EditedStoryScript(
        artifact_id="art_2",
        video_id="vid_123",
        title_variant="Test Video",
        total_word_count=500,
        beats=[],
        assets=[]
    )
    
    # Should NOT raise an exception
    result = stage.execute({"story_script": story})
    assert result.is_approved == True
    assert result.artifact_type == "QualityReport"

def test_quality_gate_hard_blocker():
    sb = MagicMock()
    # Mock DB returns 'pending_generation'
    sb.table().select().eq().execute.return_value.data = [{"status": "pending_generation"}]
    
    stage = QualityGateStage(sb, "vid_123")
    
    story = EditedStoryScript(
        artifact_id="art_3",
        video_id="vid_123",
        title_variant="Test Video",
        total_word_count=50, # Less than 100 words -> hard blocker
        beats=[],
        assets=[]
    )
    
    # Expect it to raise ValueError for script too short
    with pytest.raises(ValueError, match="Script is too short."):
        stage.execute({"story_script": story})
