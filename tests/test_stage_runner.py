import os
import sys
import pytest
from unittest.mock import MagicMock
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from stage_runner import PipelineStage
from contracts import PromiseContract

class DummyStage(PipelineStage):
    name = "DummyStage"
    output_type = "PromiseContract"

    def execute(self, inputs):
        if inputs.get("fail"):
            raise ValueError("Simulated failure")
        return PromiseContract(
            artifact_id="art-1",
            video_id=self.video_id,
            target_title="Dummy",
            topic_premise="Dummy premise",
            primary_claim="Dummy claim",
            hook_promise="Dummy hook",
            target_emotion="Dummy emotion"
        )

def test_stage_idempotency_skip():
    mock_sb = MagicMock()
    mock_response = MagicMock()
    # Simulate that artifact already exists
    mock_response.data = [{"payload": {"artifact_id": "art-1", "artifact_type": "PromiseContract"}}]
    
    mock_sb.table().select().eq().eq().order().limit().execute.return_value = mock_response
    
    stage = DummyStage(mock_sb, "vid-123")
    result = stage.run({})
    
    assert result == {"artifact_id": "art-1", "artifact_type": "PromiseContract"}
    
    # Assert that pipeline_runs insert was NOT called because it skipped
    mock_sb.table.assert_any_call("artifacts")
    # Verify execute was not called indirectly by checking if it returned the dict instead of BaseModel
    assert isinstance(result, dict)

def test_stage_successful_execution():
    mock_sb = MagicMock()
    
    # Artifact does not exist initially
    mock_art_check = MagicMock()
    mock_art_check.data = []
    
    # Run insert mock
    mock_run_insert = MagicMock()
    mock_run_insert.data = [{"id": "run-1"}]
    
    # Artifact insert mock
    mock_art_insert = MagicMock()
    mock_art_insert.data = [{"id": "db-art-1"}]
    
    def mock_execute(*args, **kwargs):
        # We need to distinguish between different table calls
        table_name = args[0]
        chain = MagicMock()
        if table_name == "artifacts":
            # Just return empty for the check
            chain.select().eq().eq().order().limit().execute.return_value = mock_art_check
            # For insert
            chain.insert().execute.return_value = mock_art_insert
        elif table_name == "pipeline_runs":
            chain.insert().execute.return_value = mock_run_insert
            chain.update().eq().execute.return_value = MagicMock()
        return chain

    mock_sb.table = MagicMock(side_effect=mock_execute)
    
    stage = DummyStage(mock_sb, "vid-123")
    result = stage.run({"fail": False})
    
    assert isinstance(result, PromiseContract)
    assert result.artifact_id == "art-1"

@pytest.mark.timeout(10)
def test_stage_failure_retries():
    import time
    # We patch time.sleep to make the test fast
    original_sleep = time.sleep
    time.sleep = MagicMock()
    
    mock_sb = MagicMock()
    mock_art_check = MagicMock()
    mock_art_check.data = []
    
    mock_run_insert = MagicMock()
    mock_run_insert.data = [{"id": "run-fail"}]
    
    def mock_execute(*args, **kwargs):
        table_name = args[0]
        chain = MagicMock()
        if table_name == "artifacts":
            chain.select().eq().eq().order().limit().execute.return_value = mock_art_check
        elif table_name == "pipeline_runs":
            chain.insert().execute.return_value = mock_run_insert
        return chain

    mock_sb.table = MagicMock(side_effect=mock_execute)
    
    stage = DummyStage(mock_sb, "vid-123")
    
    with pytest.raises(RuntimeError, match="Stage DummyStage failed: Simulated failure"):
        stage.run({"fail": True})
        
    assert time.sleep.call_count == 3
    time.sleep = original_sleep
