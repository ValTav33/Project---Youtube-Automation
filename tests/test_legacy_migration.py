import os
import json
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from contracts import StoryScript, StoryBeat, TimingMap, WordTimestamp, AssetManifest, Asset

def load_legacy_fixture():
    fixture_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 
        '../Pipeline Expansion Evaluation Plans/golden_fixture/legacy_video_row.json'
    ))
    with open(fixture_path, 'r') as f:
        return json.load(f)

def migrate_to_story_script(legacy_row: dict) -> StoryScript:
    script_payload = legacy_row.get("script_payload", {})
    scenes = script_payload.get("scenes", [])
    
    beats = []
    total_words = 0
    for scene in scenes:
        narration = scene.get("narration", "")
        word_count = len(narration.split())
        total_words += word_count
        beats.append(StoryBeat(
            beat_id=f"beat-{scene.get('scene_number')}",
            narration=narration,
            word_count=word_count,
            intent="legacy_migrated"
        ))
        
    return StoryScript(
        artifact_id=f"story-{legacy_row['id']}",
        video_id=legacy_row["id"],
        title_variant=script_payload.get("title", ""),
        beats=beats,
        total_word_count=total_words
    )

def migrate_to_timing_map(legacy_row: dict) -> TimingMap:
    timestamps = legacy_row.get("transcript_timestamps", {})
    chars = timestamps.get("characters", [])
    starts = timestamps.get("character_start_times_seconds", [])
    ends = timestamps.get("character_end_times_seconds", [])
    
    words = []
    current_word = ""
    start_time = None
    
    for idx, char in enumerate(chars):
        if start_time is None:
            start_time = starts[idx]
            
        if char == " " or idx == len(chars) - 1:
            if char != " ":
                current_word += char
            if current_word.strip():
                words.append(WordTimestamp(
                    word=current_word.strip(),
                    start=start_time,
                    end=ends[idx]
                ))
            current_word = ""
            start_time = None
        else:
            current_word += char
            
    total_duration = words[-1].end if words else 0.0
    
    return TimingMap(
        artifact_id=f"timing-{legacy_row['id']}",
        video_id=legacy_row["id"],
        words=words,
        total_duration_seconds=total_duration,
        audio_url=legacy_row.get("audio_url", "")
    )

def migrate_to_asset_manifest(legacy_row: dict) -> AssetManifest:
    script_payload = legacy_row.get("script_payload", {})
    scenes = script_payload.get("scenes", [])
    
    assets = []
    for scene in scenes:
        resolved_url = scene.get("resolved_url")
        if resolved_url:
            assets.append(Asset(
                asset_id=f"asset-{scene.get('scene_number')}",
                scene_id=f"scene-{scene.get('scene_number')}",
                asset_type="video" if ".mp4" in resolved_url else "image",
                asset_url=resolved_url,
                provider="legacy_migration"
            ))
            
    return AssetManifest(
        artifact_id=f"assets-{legacy_row['id']}",
        video_id=legacy_row["id"],
        assets=assets
    )

def test_legacy_migration():
    legacy_row = load_legacy_fixture()
    
    # Test StoryScript migration
    story_script = migrate_to_story_script(legacy_row)
    assert story_script.artifact_type == "StoryScript"
    assert len(story_script.beats) == 1
    assert story_script.beats[0].narration == "This is the story of Rome."
    
    # Test TimingMap migration
    timing_map = migrate_to_timing_map(legacy_row)
    assert timing_map.artifact_type == "TimingMap"
    assert len(timing_map.words) == 6
    assert timing_map.words[0].word == "This"
    assert timing_map.audio_url == "https://example.com/audio/rome.mp3"
    
    # Test AssetManifest migration
    asset_manifest = migrate_to_asset_manifest(legacy_row)
    assert asset_manifest.artifact_type == "AssetManifest"
    assert len(asset_manifest.assets) == 1
    assert asset_manifest.assets[0].asset_url == "https://example.com/rome_broll.mp4"
