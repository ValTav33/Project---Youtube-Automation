export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export interface VisualOverlay {
  headline?: string;
  stat_callout?: string;
  chart_type?: string;
}

export interface SceneData {
  scene_id: number;
  durationInFrames: number;
  asset_type: 'video' | 'image';
  asset_url: string;
  narration: string;
  visual_overlay?: VisualOverlay;
}

export interface VideoProps {
  scenes: SceneData[];
  words: WordTimestamp[];
  audioUrl: string;
  bgMusicUrl?: string;
  bgMusicVolume?: number;
}
