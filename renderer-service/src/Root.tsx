import React from 'react';
import { Composition } from 'remotion';
import { MainVideo } from './Composition';
import { VideoProps } from './types';

const defaultProps: VideoProps = {
  scenes: [
    {
      scene_id: 1,
      durationInFrames: 150,
      asset_type: 'image',
      asset_url: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1920&q=80',
      narration: 'Default sample scene.',
      visual_overlay: {
        headline: 'SAMPLE HEADLINE',
        stat_callout: '$100M+'
      }
    }
  ],
  words: [{ word: 'Sample', start: 0, end: 1 }],
  audioUrl: '',
  bgMusicUrl: ''
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
