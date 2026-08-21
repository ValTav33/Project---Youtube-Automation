import React from 'react';
import { Composition } from 'remotion';
import { MainVideo } from './Composition';
import { VideoProps } from './types';

const defaultProps: VideoProps = {
  scenes: [
    {
      scene_id: "scene_1",
      shot_id: "shot_1",
      durationInFrames: 90,
      asset_type: 'image',
      asset_url: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1920&q=80',
      start_frame: 0,
      end_frame: 89
    },
    {
      scene_id: "scene_2",
      shot_id: "shot_2",
      durationInFrames: 60,
      asset_type: 'video',
      asset_url: 'https://videos.pexels.com/video-files/3163534/3163534-uhd_2560_1440_30fps.mp4',
      start_frame: 90,
      end_frame: 149
    }
  ],
  words: [
    { word: 'In', start: 0.1, end: 0.3 },
    { word: 'the', start: 0.3, end: 0.5 },
    { word: 'shadows', start: 0.5, end: 1.0 },
    { word: 'of', start: 1.0, end: 1.2 },
    { word: 'global', start: 1.2, end: 1.6 },
    { word: 'finance,', start: 1.6, end: 2.2 }
  ],
  audioUrl: '',
  bgMusicUrl: '',
  fps: 30
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MainVideo"
        component={MainVideo as any}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultProps as any}
        calculateMetadata={({ props }: { props: any }) => {
          const scenes = props?.scenes || [];
          const totalFrames = scenes.reduce(
            (acc: number, scene: any) => acc + (scene?.durationInFrames || 150),
            0
          );
          return {
            durationInFrames: Math.max(totalFrames, 30),
            fps: 30,
            width: 1920,
            height: 1080
          };
        }}
      />
    </>
  );
};
