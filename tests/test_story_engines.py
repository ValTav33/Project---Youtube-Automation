import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from story_engines import PromiseStage, ResearchStage, HookStage, StoryStage, RetentionEditorStage
from contracts import PromiseContract, ResearchPacket, HookScript, StoryScript, EditedStoryScript, StoryBeat, Fact

@pytest.fixture
def mock_supabase():
    sb = MagicMock()
    # By default, mock idempotency check to return nothing (meaning stage should run)
    sb.table().select().eq().eq().order().limit().execute.return_value.data = []
    return sb

@patch('story_engines.OpenAI')
def test_promise_stage(mock_openai_cls, mock_supabase):
    mock_openai = mock_openai_cls.return_value
    mock_parsed = PromiseContract(
        artifact_id="art-1",
        video_id="vid-1",
        target_title="Title",
        topic_premise="Premise",
        primary_claim="Claim",
        hook_promise="Hook",
        target_emotion="Awe"
    )
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = mock_parsed
    mock_openai.beta.chat.completions.parse.return_value = mock_response

    stage = PromiseStage(mock_supabase, "vid-1")
    inputs = {"target_title": "Test Topic", "topic_premise": "Test Context"}
    
    result = stage.run(inputs)
    
    assert result is not None
    assert isinstance(result, PromiseContract)
    assert result.video_id == "vid-1"
    
    # Assert database calls were made to log run and save artifact
    mock_supabase.table.assert_any_call("pipeline_runs")
    mock_supabase.table.assert_any_call("artifacts")

@patch('story_engines.OpenAI')
def test_full_story_flow(mock_openai_cls, mock_supabase):
    mock_openai = mock_openai_cls.return_value
    
    # We will test HookStage and StoryStage sequentially
    promise = PromiseContract(
        artifact_id="prom-1", video_id="vid-1", target_title="T", topic_premise="P",
        primary_claim="C", hook_promise="H", target_emotion="E"
    )
    
    research = ResearchPacket(
        artifact_id="res-1", video_id="vid-1", 
        facts=[Fact(claim="F1", confidence="high"), Fact(claim="F2", confidence="high")]
    )
    
    # Test Hook
    hook_parsed = HookScript(
        artifact_id="hook-1", video_id="vid-1", title_variant="Title", total_word_count=10,
        beats=[StoryBeat(beat_id="b1", narration="Hook beat 1", word_count=3, intent="hook")]
    )
    
    mock_response = MagicMock()
    mock_response.choices[0].message.parsed = hook_parsed
    mock_openai.beta.chat.completions.parse.return_value = mock_response
    
    hook_stage = HookStage(mock_supabase, "vid-1")
    hook_result = hook_stage.run({"promise_contract": promise, "research_packet": research})
    
    assert isinstance(hook_result, HookScript)
    assert hook_result.parent_artifact_ids == [promise.artifact_id, research.artifact_id]
    
    # Test Story
    story_parsed = StoryScript(
        artifact_id="story-1", video_id="vid-1", title_variant="Title", total_word_count=50,
        beats=[StoryBeat(beat_id="b2", narration="Story beat 2", word_count=5, intent="setup")]
    )
    mock_response.choices[0].message.parsed = story_parsed
    
    story_stage = StoryStage(mock_supabase, "vid-1")
    story_result = story_stage.run({"promise_contract": promise, "research_packet": research, "hook_script": hook_result})
    
    assert isinstance(story_result, StoryScript)
    # Ensure hook beats were prepended
    assert len(story_result.beats) == 2
    assert story_result.beats[0].beat_id == "b1"
    assert story_result.beats[1].beat_id == "b2"
