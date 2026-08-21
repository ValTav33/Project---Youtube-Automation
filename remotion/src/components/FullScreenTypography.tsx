import React from 'react';
import { SceneData } from '../types';

export const FullScreenTypography: React.FC<{ scene: SceneData }> = ({ scene }) => {
  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#111',
      color: '#fff',
      fontSize: '80px',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontWeight: '900',
      textAlign: 'center',
      padding: '80px',
      letterSpacing: '-2px'
    }}>
      {/* For typography scenes, we normally use the visual_overlay, but for MVP fallback, 
          we can just show that it's a text card. Real captions handle the spoken text. */}
      [ TYPOGRAPHY BEAT ]
    </div>
  );
};
