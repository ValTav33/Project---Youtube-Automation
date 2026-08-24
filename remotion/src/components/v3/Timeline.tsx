import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface TimelineProps {
  primaryText?: string;
  secondaryText?: string;
}

export const Timeline: React.FC<TimelineProps> = ({ 
  primaryText = 'Event occurred', 
  secondaryText = '2023' 
}) => {
  const frame = useCurrentFrame();
  const enterSpring = Motion.springs.smooth(frame, 30);
  
  const lineWidth = interpolate(enterSpring, [0, 1], [0, 100]);

  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.background,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: Theme.layout.padding
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        width: '80%',
        maxWidth: 1200,
        gap: 20
      }}>
        {/* Date */}
        <div style={{
          ...Theme.typography.caption,
          color: Theme.colors.accentHighlight,
          transform: `translateX(${interpolate(enterSpring, [0, 1], [-50, 0])}px)`,
          opacity: enterSpring
        }}>
          {secondaryText}
        </div>
        
        {/* Line & Dot */}
        <div style={{ display: 'flex', alignItems: 'center', width: '100%', gap: 20 }}>
          <div style={{
            width: 24,
            height: 24,
            borderRadius: 12,
            backgroundColor: Theme.colors.accent,
            transform: `scale(${enterSpring})`
          }} />
          <div style={{
            height: 4,
            backgroundColor: Theme.colors.surfaceHighlight,
            width: `${lineWidth}%`,
            transformOrigin: 'left'
          }} />
        </div>

        {/* Event */}
        <h2 style={{
          ...Theme.typography.headline,
          color: Theme.colors.textPrimary,
          margin: 0,
          transform: `translateY(${interpolate(enterSpring, [0, 1], [50, 0])}px)`,
          opacity: enterSpring
        }}>
          {primaryText}
        </h2>
      </div>
    </AbsoluteFill>
  );
};
