import React from 'react';
import { Img, Video, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { SceneData } from '../types';

export const CinematicMedia: React.FC<{ scene: SceneData }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle Ken Burns scale effect over the duration of the scene
  const scale = interpolate(
    frame,
    [0, scene.durationInFrames],
    [1, 1.05],
    { extrapolateRight: 'clamp' }
  );

  const style: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    transform: `scale(${scale})`,
  };

  return (
    <div style={{ width: '100%', height: '100%', backgroundColor: 'black' }}>
      {scene.asset_type === 'video' ? (
        <Video src={scene.asset_url} style={style} />
      ) : (
        <Img src={scene.asset_url} style={style} />
      )}
      
      {/* Cinematic Vignette */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'radial-gradient(circle, rgba(0,0,0,0) 40%, rgba(0,0,0,0.6) 100%)',
        pointerEvents: 'none'
      }} />
    </div>
  );
};
