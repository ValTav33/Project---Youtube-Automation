import React from 'react';
import { AbsoluteFill, Img, Video, interpolate, useCurrentFrame } from 'remotion';
import { Theme } from '../../style/theme';

interface CinematicMediaProps {
  assetUrl?: string;
  motionIntention?: string;
}

export const CinematicMedia: React.FC<CinematicMediaProps> = ({ 
  assetUrl, 
  motionIntention = 'slowPan' 
}) => {
  const frame = useCurrentFrame();

  if (!assetUrl) {
    return (
      <AbsoluteFill style={{ backgroundColor: Theme.colors.surface, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <h1 style={{ ...Theme.typography.headline, color: Theme.colors.textSecondary }}>[Missing Media]</h1>
      </AbsoluteFill>
    );
  }

  const isVideo = assetUrl.endsWith('.mp4') || assetUrl.endsWith('.webm');

  // Simple ken-burns zoom effect
  const scale = motionIntention === 'static' ? 1 : interpolate(frame, [0, 300], [1, 1.15], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: Theme.colors.background, overflow: 'hidden' }}>
      {isVideo ? (
        <Video 
          src={assetUrl} 
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})` }} 
        />
      ) : (
        <Img 
          src={assetUrl} 
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})` }} 
        />
      )}
      {/* Dark vignette overlay for text readability */}
      <AbsoluteFill style={{
        background: 'radial-gradient(circle, rgba(0,0,0,0) 40%, rgba(15,23,42,0.8) 100%)'
      }} />
    </AbsoluteFill>
  );
};
