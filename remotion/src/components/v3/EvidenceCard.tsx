import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface EvidenceCardProps {
  primaryText?: string;
  secondaryText?: string;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ 
  primaryText = 'Factual claim missing', 
  secondaryText = 'Source unknown' 
}) => {
  const frame = useCurrentFrame();
  const enterSpring = Motion.springs.snappy(frame, 30);
  
  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.background,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: Theme.layout.padding
    }}>
      <div style={{
        backgroundColor: Theme.colors.surface,
        borderRadius: Theme.layout.borderRadius,
        padding: 60,
        width: '80%',
        maxWidth: 1400,
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        borderLeft: `8px solid ${Theme.colors.accent}`,
        transform: `translateY(${100 - (enterSpring * 100)}px)`,
        opacity: enterSpring,
        display: 'flex',
        flexDirection: 'column',
        gap: 30
      }}>
        <div style={{
          ...Theme.typography.caption,
          color: Theme.colors.accentHighlight,
        }}>
          VERIFIED EVIDENCE
        </div>
        
        <h2 style={{
          ...Theme.typography.headline,
          color: Theme.colors.textPrimary,
          margin: 0
        }}>
          "{primaryText}"
        </h2>
        
        <div style={{
          ...Theme.typography.body,
          color: Theme.colors.textSecondary,
          fontSize: 28,
          display: 'flex',
          alignItems: 'center',
          gap: 15
        }}>
          <div style={{ width: 40, height: 2, backgroundColor: Theme.colors.textSecondary }} />
          Source: {secondaryText}
        </div>
      </div>
    </AbsoluteFill>
  );
};
