import React from 'react';
import { Composition } from 'remotion';
import { MainVideo } from './Composition';
import { VideoProps } from './types';
import { VideoPropsSchema } from './schemas';

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

import { V3Gallery } from './V3Gallery';
import { V3MainVideo } from './V3MainVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="MainVideo"
        component={MainVideo as any}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        schema={VideoPropsSchema}
        defaultProps={defaultProps as any}
        calculateMetadata={({ props }) => {
          // Runtime WebGL safety limits and explicit Zod parsing
          const validatedProps = VideoPropsSchema.parse(props);
          
          const scenes = validatedProps.scenes || [];
          const totalFrames = scenes.reduce(
            (acc: number, scene: any) => acc + (scene?.durationInFrames || 150),
            0
          );
          return {
            durationInFrames: Math.max(totalFrames, 30),
            fps: validatedProps.fps || 30,
            width: validatedProps.width || 1080,
            height: validatedProps.height || 1920
          };
        }}
      />
      
      <Composition
        id="V3Gallery"
        component={V3Gallery}
        durationInFrames={30 * 8 * 3} // 8 components, 3 seconds each, 30fps
        fps={30}
        width={1080}
        height={1920}
      />

      <Composition
        id="V3MainVideo"
        component={V3MainVideo}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          manifest: {
            artifact_type: "ProductionManifest",
            artifact_id: "pm-mock",
            video_id: "mock",
            fps: 30,
            width: 1080,
            height: 1920,
            total_frames: 300,
            shots: [],
            audio_tracks: []
          }
        }}
        calculateMetadata={({ props }) => {
          return {
            durationInFrames: Math.max(props.manifest?.total_frames || 300, 30),
            fps: props.manifest?.fps || 30,
            width: props.manifest?.width || 1080,
            height: props.manifest?.height || 1920
          };
        }}
      />
    </>
  );
};
