import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface ComparisonProps {
  primaryText?: string;
  secondaryText?: string;
}

export const Comparison: React.FC<ComparisonProps> = ({ 
  primaryText = 'Option A', 
  secondaryText = 'Option B' 
}) => {
  const frame = useCurrentFrame();
  const enterSpring = Motion.springs.snappy(frame, 30);
  
  const splitWidth = interpolate(enterSpring, [0, 1], [0, 50]); // 50% each

  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.background,
      display: 'flex',
      flexDirection: 'row'
    }}>
      {/* Left Side */}
      <div style={{
        width: `${splitWidth}%`,
        height: '100%',
        backgroundColor: Theme.colors.surface,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        borderRight: `2px solid ${Theme.colors.background}`,
        overflow: 'hidden'
      }}>
        <h2 style={{
          ...Theme.typography.headline,
          color: Theme.colors.textPrimary,
          opacity: enterSpring,
          whiteSpace: 'nowrap'
        }}>
          {primaryText}
        </h2>
      </div>

      {/* Right Side */}
      <div style={{
        width: `${splitWidth}%`,
        height: '100%',
        backgroundColor: Theme.colors.surfaceHighlight,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        overflow: 'hidden'
      }}>
        <h2 style={{
          ...Theme.typography.headline,
          color: Theme.colors.accentHighlight,
          opacity: enterSpring,
          whiteSpace: 'nowrap'
        }}>
          {secondaryText}
        </h2>
      </div>
      
      {/* VS Badge */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: `translate(-50%, -50%) scale(${enterSpring})`,
        backgroundColor: Theme.colors.accent,
        color: Theme.colors.background,
        ...Theme.typography.caption,
        fontWeight: 800,
        padding: '20px 30px',
        borderRadius: 40,
        boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
      }}>
        VS
      </div>
    </AbsoluteFill>
  );
};
