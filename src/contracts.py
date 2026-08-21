from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Base Artifact (Inherited by all pipeline artifacts)
# -----------------------------------------------------------------------------
class BaseArtifact(BaseModel):
    """Common fields for all versioned pipeline artifacts."""
    artifact_id: str = Field(description="Unique identifier for this specific artifact version")
    video_id: str = Field(description="The parent video project ID")
    artifact_type: str = Field(description="The type of artifact (e.g. StoryScript, PromiseContract)")
    schema_version: str = Field(default="1.0.0", description="Schema version for forward compatibility")
    revision: int = Field(default=1, description="Incrementing revision number for this artifact type")
    parent_artifact_ids: List[str] = Field(default_factory=list, description="IDs of artifacts that were inputs to generate this one")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system", description="Who or what generated this artifact (e.g., 'gpt-4o', 'elevenlabs', 'human')")

# -----------------------------------------------------------------------------
# 1. Promise Contract
# -----------------------------------------------------------------------------
class PromiseContract(BaseArtifact):
    artifact_type: Literal["PromiseContract"] = "PromiseContract"
    target_title: str
    topic_premise: str
    primary_claim: str = Field(description="The core thesis or claim the video must prove")
    hook_promise: str = Field(description="What the hook must deliver in the first 30 seconds")
    target_emotion: str = Field(description="The primary emotion the viewer should feel (e.g., curiosity, outrage, awe)")

# -----------------------------------------------------------------------------
# 2. Research Packet
# -----------------------------------------------------------------------------
class Fact(BaseModel):
    claim: str
    source: Optional[str] = None
    confidence: Literal["high", "medium", "low"]

class ResearchPacket(BaseArtifact):
    artifact_type: Literal["ResearchPacket"] = "ResearchPacket"
    facts: List[Fact]
    key_statistics: List[str] = Field(default_factory=list)
    narrative_constraints: List[str] = Field(default_factory=list, description="Things to avoid or required inclusions")

# -----------------------------------------------------------------------------
# 3. Story Script
# -----------------------------------------------------------------------------
class StoryBeat(BaseModel):
    beat_id: str
    narration: str
    word_count: int
    intent: str = Field(description="The narrative purpose of this beat")

class StoryScript(BaseArtifact):
    artifact_type: Literal["StoryScript"] = "StoryScript"
    title_variant: str
    beats: List[StoryBeat]
    total_word_count: int

class HookScript(BaseArtifact):
    artifact_type: Literal["HookScript"] = "HookScript"
    title_variant: str
    beats: List[StoryBeat]
    total_word_count: int

class EditedStoryScript(BaseArtifact):
    artifact_type: Literal["EditedStoryScript"] = "EditedStoryScript"
    title_variant: str
    beats: List[StoryBeat]
    total_word_count: int

# -----------------------------------------------------------------------------
# 4. Scene Intent Plan (Pre-Audio)
# -----------------------------------------------------------------------------
class SceneIntent(BaseModel):
    scene_id: str
    beat_id: str
    visual_subject: str
    motion_intensity: Literal["static", "slow", "moderate", "fast"]
    broll_search_query: str

class SceneIntentPlan(BaseArtifact):
    artifact_type: Literal["SceneIntentPlan"] = "SceneIntentPlan"
    scenes: List[SceneIntent]

# -----------------------------------------------------------------------------
# 5. Timing Map
# -----------------------------------------------------------------------------
class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

class TimingMap(BaseArtifact):
    artifact_type: Literal["TimingMap"] = "TimingMap"
    words: List[WordTimestamp]
    total_duration_seconds: float
    audio_url: str = Field(description="URL to the generated speech audio")

# -----------------------------------------------------------------------------
# 6. Shot Plan (Post-Audio, Merged with Scene Intent)
# -----------------------------------------------------------------------------
class Shot(BaseModel):
    shot_id: str
    scene_id: str
    start_frame: int
    end_frame: int
    duration_frames: int

class ShotPlan(BaseArtifact):
    artifact_type: Literal["ShotPlan"] = "ShotPlan"
    shots: List[Shot]
    fps: int = 30

# -----------------------------------------------------------------------------
# 7. Asset Manifest
# -----------------------------------------------------------------------------
class Asset(BaseModel):
    asset_id: str
    scene_id: str
    asset_type: Literal["video", "image"]
    asset_url: str
    provider: str = Field(description="e.g., 'pexels', 'fal', 'placeholder'")

class AssetManifest(BaseArtifact):
    artifact_type: Literal["AssetManifest"] = "AssetManifest"
    assets: List[Asset]

# -----------------------------------------------------------------------------
# 8. Audio Plan
# -----------------------------------------------------------------------------
class AudioCue(BaseModel):
    cue_id: str
    start_time_seconds: float
    asset_url: str
    volume: float = 1.0
    cue_type: Literal["music", "sfx"]

class AudioPlan(BaseArtifact):
    artifact_type: Literal["AudioPlan"] = "AudioPlan"
    cues: List[AudioCue]

# -----------------------------------------------------------------------------
# 9. Quality Report
# -----------------------------------------------------------------------------
class QualityFinding(BaseModel):
    artifact_id: str
    severity: Literal["blocker", "warning", "info"]
    issue: str
    suggested_correction: Optional[str]

class QualityReport(BaseArtifact):
    artifact_type: Literal["QualityReport"] = "QualityReport"
    is_approved: bool
    findings: List[QualityFinding]

# -----------------------------------------------------------------------------
# 10. Publish Package
# -----------------------------------------------------------------------------
class PublishPackage(BaseArtifact):
    artifact_type: Literal["PublishPackage"] = "PublishPackage"
    title: str
    description: str
    tags: List[str]
    thumbnail_urls: List[str]
    privacy_status: Literal["public", "unlisted", "private"]

# -----------------------------------------------------------------------------
# 11. Analytics Feature Vector
# -----------------------------------------------------------------------------
class AnalyticsFeatureVector(BaseArtifact):
    artifact_type: Literal["AnalyticsFeatureVector"] = "AnalyticsFeatureVector"
    topic_category: str
    hook_type: str
    hook_duration_seconds: float
    total_shots: int
    music_profile: str
