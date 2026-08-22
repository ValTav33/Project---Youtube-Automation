import pytest
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from scene_director import ShotStage
from contracts import (
    EditedStoryScript,
    StoryBeat,
    SceneIntentPlan,
    SceneIntent,
    TimingMap,
    WordTimestamp,
    ShotPlan
)

@pytest.fixture
def mock_supabase():
    sb = MagicMock()
    sb.table().select().eq().eq().order().limit().execute.return_value.data = []
    return sb

def test_shot_compilation(mock_supabase):
    stage = ShotStage(mock_supabase, "vid-1")
    
    # Mock EditedStoryScript (2 beats, 10 words total)
    story = EditedStoryScript(
        artifact_id="art-1", video_id="vid-1", title_variant="Title", total_word_count=10,
        beats=[
            StoryBeat(beat_id="b1", narration="A short intro.", word_count=3, intent="hook"),
            StoryBeat(beat_id="b2", narration="This is a longer beat with more words.", word_count=7, intent="setup")
        ]
    )
    
    # Mock SceneIntentPlan (3 scenes)
    intent = SceneIntentPlan(
        artifact_id="int-1", video_id="vid-1",
        scenes=[
            SceneIntent(scene_id="s1", beat_id="b1", visual_subject="A", motion_intensity="fast", broll_search_query="A"),
            SceneIntent(scene_id="s2", beat_id="b2", visual_subject="B", motion_intensity="slow", broll_search_query="B"),
            SceneIntent(scene_id="s3", beat_id="b2", visual_subject="C", motion_intensity="slow", broll_search_query="C")
        ]
    )
    
    # Mock TimingMap (10 seconds total audio)
    timing = TimingMap(
        artifact_id="tim-1", video_id="vid-1", audio_url="url",
        total_duration_seconds=10.0,
        words=[WordTimestamp(word="w", start=i, end=i+1) for i in range(10)]
    )
    
    result = stage.run({
        "scene_intent": intent,
        "timing_map": timing,
        "story_script": story
    })
    
    assert isinstance(result, ShotPlan)
    assert len(result.shots) == 3
    
    # Total frames = 10 seconds * 30 fps = 300 frames
    # beat 1 ratio = 3/10 = 90 frames
    # beat 2 ratio = 7/10 = 210 frames
    
    # scene 1 is mapped to beat 1 -> duration = 90 frames
    assert result.shots[0].scene_id == "s1"
    assert result.shots[0].duration_frames == 90
    assert result.shots[0].start_frame == 0
    assert result.shots[0].end_frame == 89
    
    # scene 2 is mapped to beat 2 -> duration = 105 frames
    assert result.shots[1].scene_id == "s2"
    assert result.shots[1].duration_frames == 105
    assert result.shots[1].start_frame == 90
    assert result.shots[1].end_frame == 194
    
    # scene 3 is mapped to beat 2 -> duration = 105 frames
    assert result.shots[2].scene_id == "s3"
    assert result.shots[2].duration_frames == 105
    assert result.shots[2].start_frame == 195
    assert result.shots[2].end_frame == 299
