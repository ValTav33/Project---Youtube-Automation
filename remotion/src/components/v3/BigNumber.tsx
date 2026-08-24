import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface BigNumberProps {
  primaryText?: string;
  secondaryText?: string;
}

export const BigNumber: React.FC<BigNumberProps> = ({ 
  primaryText = '0', 
  secondaryText = 'Metric' 
}) => {
  const frame = useCurrentFrame();
  const enterSpring = Motion.springs.bouncy(frame, 30);
  
  // Extract number if possible to do a count up, else just show it
  const numMatch = primaryText.match(/([\d,\.]+)/);
  const isNumeric = numMatch !== null;
  
  // If it's a clean number, we can animate it. For simplicity in V3 baseline, 
  // we'll just scale it in with a spring.
  
  const scale = interpolate(enterSpring, [0, 1], [0.5, 1]);
  const opacity = interpolate(enterSpring, [0, 1], [0, 1]);

  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.background,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexDirection: 'column',
      gap: 20
    }}>
      <h1 style={{
        ...Theme.typography.title,
        fontSize: 240,
        color: Theme.colors.accent,
        margin: 0,
        transform: `scale(${scale})`,
        opacity
      }}>
        {primaryText}
      </h1>
      
      <h3 style={{
        ...Theme.typography.headline,
        color: Theme.colors.textPrimary,
        margin: 0,
        opacity: interpolate(frame, [10, 20], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
        transform: `translateY(${interpolate(frame, [10, 20], [20, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px)`
      }}>
        {secondaryText}
      </h3>
    </AbsoluteFill>
  );
};
