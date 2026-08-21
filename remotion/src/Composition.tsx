import React from 'react';
import {
  AbsoluteFill,
  Series,
  Audio
} from 'remotion';
import { VideoProps } from './types';
import { ComponentRegistry } from './components/Registry';
import { Captions } from './components/Captions';

export const MainVideo: React.FC<VideoProps> = ({
  scenes,
  words,
  audioUrl,
  bgMusicUrl,
  bgMusicVolume = 0.12
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000000' }}>
      {/* Visual Component Sequence mapped through the Registry */}
      <Series>
        {scenes.map(scene => (
          <Series.Sequence
            key={scene.shot_id} // using shot_id to avoid key collisions
            durationInFrames={scene.durationInFrames}
          >
            <ComponentRegistry scene={scene} />
          </Series.Sequence>
        ))}
      </Series>

      {/* Semantic Kinetic Captions Overlay */}
      {words && words.length > 0 && <Captions words={words} />}

      {/* Master Voiceover Audio */}
      {audioUrl && <Audio src={audioUrl} volume={1.0} />}

      {/* Ambient Background Music */}
      {bgMusicUrl && <Audio src={bgMusicUrl} volume={bgMusicVolume} loop />}
    </AbsoluteFill>
  );
};
