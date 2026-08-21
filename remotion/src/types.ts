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
