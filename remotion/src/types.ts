export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export interface SceneData {
  scene_id: string;
  shot_id: string;
  durationInFrames: number;
  asset_type: 'video' | 'image';
  asset_url: string;
  start_frame: number;
  end_frame: number;
}

export interface VideoProps {
  scenes: SceneData[];
  words: WordTimestamp[];
  audioUrl: string;
  bgMusicUrl?: string;
  bgMusicVolume?: number;
  fps?: number;
}

import { z } from "zod";
import * as schemas from "./schemas";

export type BaseArtifact = z.infer<typeof schemas.BaseArtifactSchema>;
export type PromiseContract = z.infer<typeof schemas.PromiseContractSchema>;
export type ResearchPacket = z.infer<typeof schemas.ResearchPacketSchema>;
export type StoryScript = z.infer<typeof schemas.StoryScriptSchema>;
export type HookScript = z.infer<typeof schemas.HookScriptSchema>;
export type EditedStoryScript = z.infer<typeof schemas.EditedStoryScriptSchema>;
export type SceneIntentPlan = z.infer<typeof schemas.SceneIntentPlanSchema>;
export type TimingMap = z.infer<typeof schemas.TimingMapSchema>;
export type ShotPlan = z.infer<typeof schemas.ShotPlanSchema>;
export type AssetManifest = z.infer<typeof schemas.AssetManifestSchema>;
export type AudioPlan = z.infer<typeof schemas.AudioPlanSchema>;
export type QualityReport = z.infer<typeof schemas.QualityReportSchema>;
export type PublishPackage = z.infer<typeof schemas.PublishPackageSchema>;
export type AnalyticsFeatureVector = z.infer<typeof schemas.AnalyticsFeatureVectorSchema>;
