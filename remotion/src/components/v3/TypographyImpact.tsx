import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface TypographyImpactProps {
  primaryText?: string;
}

export const TypographyImpact: React.FC<TypographyImpactProps> = ({ 
  primaryText = 'IMPACT' 
}) => {
  const frame = useCurrentFrame();
  const enterSpring = Motion.springs.bouncy(frame, 30);

  // Subtle continuous scale
  const continuousScale = interpolate(frame, [0, 300], [1, 1.1]);

  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.accent, // Use accent color as background for impact
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: Theme.layout.padding
    }}>
      <h1 style={{
        ...Theme.typography.title,
        color: Theme.colors.background, // Invert colors
        fontSize: 140,
        textAlign: 'center',
        textTransform: 'uppercase',
        transform: `scale(${enterSpring * continuousScale})`,
        opacity: interpolate(enterSpring, [0, 0.5], [0, 1]),
        textShadow: '0 20px 40px rgba(0,0,0,0.3)'
      }}>
        {primaryText}
      </h1>
    </AbsoluteFill>
  );
};
