import { z } from 'zod';

export const BaseArtifactSchema = z.object({
  artifact_id: z.string(),
  video_id: z.string(),
  artifact_type: z.string(),
  schema_version: z.string().default("1.0.0"),
  revision: z.number().default(1),
  parent_artifact_ids: z.array(z.string()).default([]),
  created_at: z.string(),
  created_by: z.string().default("system"),
});

export const PromiseContractSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("PromiseContract"),
  target_title: z.string(),
  topic_premise: z.string(),
  primary_claim: z.string(),
  hook_promise: z.string(),
  target_emotion: z.string(),
});

export const FactSchema = z.object({
  claim: z.string(),
  source: z.string().nullable().optional(),
  confidence: z.enum(["high", "medium", "low"]),
});

export const ResearchPacketSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("ResearchPacket"),
  facts: z.array(FactSchema),
  key_statistics: z.array(z.string()).default([]),
  narrative_constraints: z.array(z.string()).default([]),
});

export const StoryBeatSchema = z.object({
  beat_id: z.string(),
  narration: z.string(),
  word_count: z.number(),
  intent: z.string(),
});

export const StoryScriptSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("StoryScript"),
  title_variant: z.string(),
  beats: z.array(StoryBeatSchema),
  total_word_count: z.number(),
});

export const HookScriptSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("HookScript"),
  title_variant: z.string(),
  beats: z.array(StoryBeatSchema),
  total_word_count: z.number(),
});

export const EditedStoryScriptSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("EditedStoryScript"),
  title_variant: z.string(),
  beats: z.array(StoryBeatSchema),
  total_word_count: z.number(),
});

export const SceneIntentSchema = z.object({
  scene_id: z.string(),
  beat_id: z.string(),
  visual_subject: z.string(),
  motion_intensity: z.enum(["static", "slow", "moderate", "fast"]),
  broll_search_query: z.string(),
});

export const SceneIntentPlanSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("SceneIntentPlan"),
  scenes: z.array(SceneIntentSchema),
});

export const WordTimestampSchema = z.object({
  word: z.string(),
  start: z.number(),
  end: z.number(),
});

export const TimingMapSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("TimingMap"),
  words: z.array(WordTimestampSchema),
  total_duration_seconds: z.number(),
  audio_url: z.string(),
});

export const ShotSchema = z.object({
  shot_id: z.string(),
  scene_id: z.string(),
  start_frame: z.number(),
  end_frame: z.number(),
  duration_frames: z.number(),
});

export const ShotPlanSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("ShotPlan"),
  shots: z.array(ShotSchema),
  fps: z.number().default(30),
});

export const AssetSchema = z.object({
  asset_id: z.string(),
  scene_id: z.string(),
  asset_type: z.enum(["video", "image"]),
  asset_url: z.string(),
  provider: z.string(),
});

export const AssetManifestSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("AssetManifest"),
  assets: z.array(AssetSchema),
});

export const AudioCueSchema = z.object({
  cue_id: z.string(),
  start_time_seconds: z.number(),
  asset_url: z.string(),
  volume: z.number().default(1.0),
  cue_type: z.enum(["music", "sfx"]),
});

export const AudioPlanSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("AudioPlan"),
  cues: z.array(AudioCueSchema),
});

export const QualityFindingSchema = z.object({
  artifact_id: z.string(),
  severity: z.enum(["blocker", "warning", "info"]),
  issue: z.string(),
  suggested_correction: z.string().nullable().optional(),
});

export const QualityReportSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("QualityReport"),
  is_approved: z.boolean(),
  findings: z.array(QualityFindingSchema),
});

export const PublishPackageSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("PublishPackage"),
  title: z.string(),
  description: z.string(),
  tags: z.array(z.string()),
  thumbnail_urls: z.array(z.string()),
  privacy_status: z.enum(["public", "unlisted", "private"]),
});

export const AnalyticsFeatureVectorSchema = BaseArtifactSchema.extend({
  artifact_type: z.literal("AnalyticsFeatureVector"),
  topic_category: z.string(),
  hook_type: z.string(),
  hook_duration_seconds: z.number(),
  total_shots: z.number(),
  first_minute_shot_count: z.number(),
  open_loop_count: z.number(),
  music_profile: z.string(),
  title_strategy: z.string(),
  thumbnail_strategy: z.string(),
  style_profile_version: z.string(),
});

export const RemotionSceneSchema = z.object({
  scene_id: z.string(),
  shot_id: z.string(),
  durationInFrames: z.number(),
  asset_type: z.enum(["video", "image"]),
  asset_url: z.string(),
  start_frame: z.number(),
  end_frame: z.number(),
});

export const VideoPropsSchema = z.object({
  scenes: z.array(RemotionSceneSchema),
  words: z.array(WordTimestampSchema),
  audioUrl: z.string(),
  bgMusicUrl: z.string().optional(),
  bgMusicVolume: z.number().optional(),
  fps: z.number().max(60, "FPS exceeds safety limits").optional(),
  width: z.number().max(1920, "Resolution width exceeds 1080p limit").optional(),
  height: z.number().max(1080, "Resolution height exceeds 1080p limit").optional()
});

