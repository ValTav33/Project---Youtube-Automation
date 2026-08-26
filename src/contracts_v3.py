from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Base Artifact (V3)
# -----------------------------------------------------------------------------
class BaseArtifactV3(BaseModel):
    """Common fields for all versioned V3 pipeline artifacts."""
    artifact_id: str = Field(description="Unique identifier for this specific artifact version")
    video_id: str = Field(description="The parent video project ID")
    artifact_type: str = Field(description="The type of artifact")
    schema_version: str = Field(default="3.0.0", description="Schema version")
    revision: int = Field(default=1, description="Incrementing revision number for this artifact type")
    parent_artifact_ids: List[str] = Field(default_factory=list, description="IDs of artifacts that were inputs to generate this one")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = Field(default="system", description="Agent or process that generated this artifact")

# -----------------------------------------------------------------------------
# 1. Channel Creative Bible
# -----------------------------------------------------------------------------
class ChannelCreativeBible(BaseArtifactV3):
    artifact_type: Literal["ChannelCreativeBible"] = "ChannelCreativeBible"
    channel_identity: str = Field(description="Core identity and tone of the channel")
    target_audience: str = Field(description="Detailed description of the target audience")
    visual_rules: str = Field(description="Rules for visuals, colors, and framing")
    caption_policy: str = Field(description="When and how captions should be displayed")
    source_policy: str = Field(description="Requirements for source citations and fact-checking")
    prohibited_cliches: List[str] = Field(description="Words, phrases, or visual tropes to avoid")

# -----------------------------------------------------------------------------
# 2. Video Brief
# -----------------------------------------------------------------------------
class VideoBrief(BaseArtifactV3):
    artifact_type: Literal["VideoBrief"] = "VideoBrief"
    topic: str
    target_duration_seconds: int
    promise: str = Field(description="What this video promises the viewer")
    audience_tension: str = Field(description="The tension or curiosity gap")
    title_hypothesis: str
    thumbnail_hypothesis: str
    creative_bible_version: str = Field(description="Reference to the active Creative Bible version")

# -----------------------------------------------------------------------------
# 2.5 Thumbnail Plan
# -----------------------------------------------------------------------------
class ThumbnailPlan(BaseArtifactV3):
    artifact_type: Literal["ThumbnailPlan"] = "ThumbnailPlan"
    optimized_image_prompt: str = Field(description="The optimized DALL-E 3 image generation prompt")
    generated_url: Optional[str] = Field(default=None, description="The URL of the generated image")

# -----------------------------------------------------------------------------
# 3. Verified Research Packet
# -----------------------------------------------------------------------------
class VerifiedClaim(BaseModel):
    claim_id: str
    claim_text: str
    source_url: str
    publisher: str
    publication_date: str
    evidence_note: str
    confidence: Literal["high", "medium", "low"]

class VerifiedResearchPacket(BaseArtifactV3):
    artifact_type: Literal["VerifiedResearchPacket"] = "VerifiedResearchPacket"
    claims: List[VerifiedClaim]

# -----------------------------------------------------------------------------
# 4. Story Blueprint
# -----------------------------------------------------------------------------
class NarrativeBeat(BaseModel):
    beat_id: str
    narration_text: str
    tension_level: Literal["low", "medium", "high"] = Field(description="Intended audience tension at this beat")
    claim_references: List[str] = Field(description="List of claim_ids from VerifiedResearchPacket used in this beat")
    intended_payoff: str = Field(description="How this beat pays off or builds towards the promise")
    word_count: int

class StoryBlueprint(BaseArtifactV3):
    artifact_type: Literal["StoryBlueprint"] = "StoryBlueprint"
    beats: List[NarrativeBeat]
    total_word_count: int

# -----------------------------------------------------------------------------
# 5. Visual Brief Plan
# -----------------------------------------------------------------------------
class VisualComponentChoice(BaseModel):
    component_type: Literal[
        "CinematicMedia", "EvidenceCard", "BigNumber", "DataChart", 
        "Timeline", "Comparison", "ProductScreen", "TypographyImpact"
    ]
    primary_text: Optional[str] = None
    secondary_text: Optional[str] = None
    asset_query: Optional[str] = Field(description="Query to find the primary background/asset if applicable")
    fallback_component_type: Optional[str] = None

class VisualBeat(BaseModel):
    beat_id: str = Field(description="Must map 1:1 to NarrativeBeat beat_id")
    visual_argument: str = Field(description="What the visual is arguing or showing")
    evidence_type: str = Field(description="Type of evidence being shown")
    component_choice: VisualComponentChoice
    visual_role: str = Field(description="Role of this visual (e.g. b-roll, hero, chart)")
    emphasis_policy: str = Field(description="How to emphasize (e.g. slight zoom, highlight word)")
    motion_intention: str = Field(description="Intended motion (static, slow pan, dynamic)")
    source_claim_ids: List[str] = Field(default_factory=list, description="Linked facts if the visual is data/evidence")

class VisualBriefPlan(BaseArtifactV3):
    artifact_type: Literal["VisualBriefPlan"] = "VisualBriefPlan"
    visual_beats: List[VisualBeat]

# -----------------------------------------------------------------------------
# 6. Asset Manifest
# -----------------------------------------------------------------------------
class ResolvedAsset(BaseModel):
    beat_id: str
    asset_url: str
    provider: str
    license_category: str

class AssetManifest(BaseArtifactV3):
    artifact_type: Literal["AssetManifest"] = "AssetManifest"
    resolved_assets: List[ResolvedAsset]

# -----------------------------------------------------------------------------
# 7. Audio Plan
# -----------------------------------------------------------------------------
class AudioPlan(BaseArtifactV3):
    artifact_type: Literal["AudioPlan"] = "AudioPlan"
    music_track_url: str
    voice_track_url: Optional[str] = None
    total_duration_seconds: float = Field(default=0.0)
    sfx_cues: List[Dict[str, Any]] = Field(default_factory=list)
    word_timestamps: List[Dict[str, Any]] = Field(default_factory=list, description="Word-level timestamps for dynamic subtitles")

# -----------------------------------------------------------------------------
# 8. Production Manifest (Renderer Input)
# -----------------------------------------------------------------------------
class RenderShot(BaseModel):
    shot_id: str
    start_frame: int
    duration_frames: int
    component_type: str
    component_props: Dict[str, Any] = Field(description="Resolved props for the Remotion component")
    asset_url: Optional[str] = Field(default=None, description="Resolved media URL")
    provenance: Optional[Dict[str, str]] = Field(default=None, description="Origin of external media")

class AudioTrack(BaseModel):
    track_id: str
    audio_type: Literal["narration", "music", "sfx"]
    asset_url: str
    start_frame: int
    duration_frames: int
    volume: float

class ProductionManifest(BaseArtifactV3):
    artifact_type: Literal["ProductionManifest"] = "ProductionManifest"
    fps: int = 30
    width: int = 1080
    height: int = 1920
    total_frames: int
    shots: List[RenderShot]
    audio_tracks: List[AudioTrack]
    word_timestamps: List[Dict[str, Any]] = Field(default_factory=list, description="Word-level timestamps for dynamic subtitles")

# -----------------------------------------------------------------------------
# 9. Repair & QA
# -----------------------------------------------------------------------------
class RepairRequest(BaseModel):
    beat_id: str
    issue_type: Literal["asset_replacement", "caption_reduction", "timing_adjustment", "component_change"]
    description: str

class EditorRepairPlan(BaseArtifactV3):
    artifact_type: Literal["EditorRepairPlan"] = "EditorRepairPlan"
    target_manifest_id: str
    repairs: List[RepairRequest]

class ReviewPackage(BaseArtifactV3):
    artifact_type: Literal["ReviewPackage"] = "ReviewPackage"
    manifest_id: str
    title: str
    thumbnail_url: Optional[str] = None
    diagnostics: Dict[str, Any] = Field(default_factory=dict)

# -----------------------------------------------------------------------------
# 10. Analytics & ML Feedback Loop
# -----------------------------------------------------------------------------
class CreativeFeatureVector(BaseArtifactV3):
    """The 'DNA' of the video extracted for ML correlation."""
    artifact_type: Literal["CreativeFeatureVector"] = "CreativeFeatureVector"
    hook_type: str = Field(description="Categorization of the first 5 seconds")
    promise_category: str = Field(description="Type of promise made (e.g. monetary, curiosity)")
    component_distribution: Dict[str, int] = Field(description="Count of each component type used")
    visual_density: float = Field(description="Shots per minute")

class YouTubeAnalyticsSnapshot(BaseArtifactV3):
    """Ingested metrics at a specific point in time (e.g. 24h, 7d)."""
    artifact_type: Literal["YouTubeAnalyticsSnapshot"] = "YouTubeAnalyticsSnapshot"
    interval: Literal["24h", "7d", "30d", "lifetime"]
    impressions: int
    ctr_percent: float
    average_view_duration_seconds: int
    retention_30s_percent: float
    retention_50pct_percent: float
