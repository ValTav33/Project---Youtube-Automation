import os
import json
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from orchestrator import prepare_remotion_props, execute_local_remotion_render, run_pipeline_for_video

@pytest.fixture
def golden_video():
    fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures/golden_video.json')
    with open(fixture_path, 'r') as f:
        return json.load(f)

def test_prepare_remotion_props(golden_video):
    """Test that remotion props are correctly built from the golden video fixture."""
    props = prepare_remotion_props(golden_video)
    
    assert "scenes" in props
    assert "words" in props
    assert "audioUrl" in props
    
    # Check that scenes have expected fields
    scenes = props["scenes"]
    assert len(scenes) > 0
    first_scene = scenes[0]
    assert "scene_id" in first_scene
    assert "durationInFrames" in first_scene
    assert "asset_type" in first_scene
    assert "asset_url" in first_scene
    assert "narration" in first_scene

@patch('subprocess.Popen')
@patch('orchestrator.get_supabase')
def test_execute_local_remotion_render(mock_get_supabase, mock_popen, golden_video):
    """Test that execute_local_remotion_render builds the right command and completes."""
    
    # Mock subprocess returning 0
    mock_process = MagicMock()
    mock_process.stdout = ["Rendered 10/100", "Rendered 100/100"]
    mock_process.returncode = 0
    mock_popen.return_value = mock_process
    
    # Mock Supabase
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb
    mock_sb.table().select().eq().single().execute.return_value.data = {"script_payload": golden_video.get("script_payload", {})}
    
    props = prepare_remotion_props(golden_video)
    video_id = golden_video.get("id", "test_id")
    
    success = execute_local_remotion_render(video_id, props)
    
    assert success is True
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    
    cmd = args[0]
    assert "npx" in cmd
    assert "remotion" in cmd
    assert "render" in cmd
    
@patch('orchestrator.get_supabase')
@patch('orchestrator.process_video_scripting')
@patch('orchestrator.process_video_audio')
@patch('orchestrator.process_video_asset_resolution')
@patch('orchestrator.process_video_publishing_preparation')
@patch('orchestrator.execute_local_remotion_render')
@patch('publisher.publish_to_youtube')
@patch('orchestrator.notify_pipeline_start')
@patch('orchestrator.notify_step_complete')
@patch('orchestrator.notify_render_complete')
def test_run_pipeline_for_video(
    mock_notify_render, mock_notify_step, mock_notify_start,
    mock_publish, mock_render, mock_prepare, mock_asset, mock_audio, mock_scripting, mock_get_supabase, golden_video
):
    """Test the main orchestrator loop using the golden fixture data."""
    
    # Setup mock supabase to return the golden video
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb
    mock_response = MagicMock()
    mock_response.data = golden_video
    mock_sb.table().select().eq().single().execute.return_value = mock_response
    
    # Setup success returns
    mock_render.return_value = True
    mock_publish.return_value = True
    
    video_id = golden_video.get("id", "test_id")
    run_pipeline_for_video(video_id)
    
    # Assert sequence
    mock_notify_start.assert_called_once()
    mock_scripting.assert_called_once_with(video_id)
    mock_audio.assert_called_once_with(video_id)
    mock_asset.assert_called_once_with(video_id)
    mock_prepare.assert_called_once_with(video_id)
    mock_render.assert_called_once()
    mock_publish.assert_called_once_with(video_id)
