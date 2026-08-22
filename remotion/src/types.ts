import { z } from "zod";
import * as schemas from "./schemas";

export type WordTimestamp = z.infer<typeof schemas.WordTimestampSchema>;
export type SceneData = z.infer<typeof schemas.RemotionSceneSchema>;
export type VideoProps = z.infer<typeof schemas.VideoPropsSchema>;

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
