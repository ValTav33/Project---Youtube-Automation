import React from 'react';
import { AbsoluteFill, Img, useCurrentFrame, interpolate } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface ProductScreenProps {
  primaryText?: string;
  assetUrl?: string;
}

export const ProductScreen: React.FC<ProductScreenProps> = ({ 
  primaryText = 'Product UI', 
  assetUrl 
}) => {
  const frame = useCurrentFrame();
  const enterSpring = Motion.springs.smooth(frame, 30);
  
  const translateY = interpolate(enterSpring, [0, 1], [200, 0]);

  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.background,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      padding: Theme.layout.padding
    }}>
      <h2 style={{
        ...Theme.typography.headline,
        color: Theme.colors.textPrimary,
        marginBottom: 60,
        opacity: enterSpring
      }}>
        {primaryText}
      </h2>

      {/* Stylized Browser / Device Frame */}
      <div style={{
        width: '80%',
        height: '60%',
        backgroundColor: Theme.colors.surface,
        borderRadius: 16,
        boxShadow: '0 30px 60px rgba(0,0,0,0.6)',
        border: `1px solid ${Theme.colors.surfaceHighlight}`,
        overflow: 'hidden',
        transform: `translateY(${translateY}px) scale(${interpolate(enterSpring, [0, 1], [0.95, 1])})`,
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Mock Title bar */}
        <div style={{ 
          height: 40, 
          backgroundColor: Theme.colors.surfaceHighlight,
          display: 'flex',
          alignItems: 'center',
          padding: '0 20px',
          gap: 10
        }}>
          <div style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: Theme.colors.danger }} />
          <div style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: '#F59E0B' }} />
          <div style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: Theme.colors.success }} />
        </div>
        
        {/* Content */}
        <div style={{ flex: 1, backgroundColor: '#ffffff', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          {assetUrl ? (
            <Img src={assetUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <div style={{ ...Theme.typography.body, color: '#94A3B8' }}>
              [Screenshot Missing]
            </div>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
