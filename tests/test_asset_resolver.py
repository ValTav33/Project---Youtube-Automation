import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from asset_resolver import AssetResolutionStage
from contracts import SceneIntentPlan, SceneIntent, AssetManifest

@pytest.fixture
def mock_supabase():
    sb = MagicMock()
    sb.table().select().eq().eq().order().limit().execute.return_value.data = []
    return sb

@patch('asset_resolver.resolve_all_scene_assets')
def test_asset_resolution_stage(mock_resolve, mock_supabase):
    # Mock the async resolution
    mock_resolve.return_value = [
        {
            "scene_id": "scene_1",
            "asset_type": "video",
            "asset_url": "https://pexels.com/video.mp4"
        },
        {
            "scene_id": "scene_2",
            "asset_type": "image",
            "asset_url": "https://fal.ai/image.jpg"
        }
    ]
    
    intent_plan = SceneIntentPlan(
        artifact_id="intent-1",
        video_id="vid-1",
        scenes=[
            SceneIntent(scene_id="scene_1", beat_id="b1", visual_subject="A", motion_intensity="fast", broll_search_query="A"),
            SceneIntent(scene_id="scene_2", beat_id="b2", visual_subject="B", motion_intensity="slow", broll_search_query="B")
        ]
    )
    
    stage = AssetResolutionStage(mock_supabase, "vid-1")
    result = stage.run({"scene_intent": intent_plan})
    
    assert isinstance(result, AssetManifest)
    assert len(result.assets) == 2
    
    assert result.assets[0].scene_id == "scene_1"
    assert result.assets[0].provider == "pexels"
    assert result.assets[0].asset_url == "https://pexels.com/video.mp4"
    
    assert result.assets[1].scene_id == "scene_2"
    assert result.assets[1].provider == "fal.ai"
    assert result.assets[1].asset_type == "image"
