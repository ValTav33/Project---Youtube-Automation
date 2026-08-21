import React from 'react';
import { SceneData } from '../types';
import { CinematicMedia } from './CinematicMedia';
import { FullScreenTypography } from './FullScreenTypography';

// Fallback component when an unsupported type is requested
const UnsupportedDirective: React.FC<{ scene: SceneData }> = ({ scene }) => {
  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#ff0055',
      color: 'white',
      fontSize: '60px',
      fontFamily: 'sans-serif',
      fontWeight: 'bold',
      textAlign: 'center',
      padding: '40px'
    }}>
      UNSUPPORTED COMPONENT: <br />
      {scene.asset_type}
    </div>
  );
};

export const ComponentRegistry: React.FC<{ scene: SceneData }> = ({ scene }) => {
  // Safe routing based on asset_type
  switch (scene.asset_type) {
    case 'video':
    case 'image':
      if (scene.asset_url) {
        return <CinematicMedia scene={scene} />;
      }
      // If there's an image/video request but NO URL, fallback to Typography
      return <FullScreenTypography scene={scene} />;
      
    case 'typography':
      return <FullScreenTypography scene={scene} />;
      
    default:
      // In production, fallback to a safe text-card rather than crashing
      return <UnsupportedDirective scene={scene} />;
  }
};
