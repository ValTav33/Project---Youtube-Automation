import React from 'react';
import {
  AbsoluteFill,
  Series,
  OffthreadVideo,
  Img,
  Audio,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
  staticFile
} from 'remotion';
import { VideoProps, SceneData, WordTimestamp } from './types';

const resolveMediaSrc = (src: string) => {
  if (!src) return '';
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:') || src.startsWith('blob:')) {
    return src;
  }
  return staticFile(src);
};

// Word-level Animated Subtitle Component
const SubtitlesOverlay: React.FC<{ words: WordTimestamp[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (!words || words.length === 0) return null;

  const activeIndex = words.findIndex(w => currentTime >= w.start && currentTime <= w.end);
  if (activeIndex === -1) return null;

  const visibleSlice = words.slice(
    Math.max(0, activeIndex - 1),
    Math.min(words.length, activeIndex + 2)
  );

  return (
    <div
      style={{
        position: 'absolute',
        bottom: '12%',
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        gap: '14px',
        fontFamily: 'Inter, Helvetica, sans-serif',
        fontSize: '52px',
        fontWeight: 900,
        textTransform: 'uppercase',
        textShadow: '0 4px 20px rgba(0,0,0,0.95), 0 2px 6px rgba(0,0,0,0.8)'
      }}
    >
      {visibleSlice.map((w, idx) => {
        const isActive = currentTime >= w.start && currentTime <= w.end;
        return (
          <span
            key={idx}
            style={{
              color: isActive ? '#FFE600' : '#FFFFFF',
              transform: isActive ? 'scale(1.15)' : 'scale(1.0)',
              transition: 'transform 0.05s ease-out',
              display: 'inline-block'
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};

// Scene Component with Ken Burns Zoom & Stat Pop-ins
const SceneItem: React.FC<{ scene: SceneData }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns dynamic zoom
  const scale = interpolate(frame, [0, scene.durationInFrames], [1.0, 1.15], {
    extrapolateRight: 'clamp'
  });

  const statProgress = spring({
    frame,
    fps,
    config: { damping: 12, mass: 0.8, stiffness: 100 }
  });

  return (
    <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: '#0B0F19' }}>
      {scene.asset_type === 'video' ? (
        <OffthreadVideo
          src={resolveMediaSrc(scene.asset_url)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale})`
          }}
          muted
          onError={(e) => {
            console.warn(`Video playback error in scene #${scene.scene_id}:`, e);
          }}
        />
      ) : (
        <Img
          src={resolveMediaSrc(scene.asset_url)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale})`
          }}
          onError={(e) => {
            console.warn(`Image load error in scene #${scene.scene_id}:`, e);
          }}
        />
      )}

      {/* Dark Vignette Overlay */}
      <AbsoluteFill
        style={{
          background: 'radial-gradient(circle, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.85) 100%)'
        }}
      />

      {/* Dynamic Stat Callout */}
      {scene.visual_overlay?.stat_callout && (
        <div
          style={{
            position: 'absolute',
            top: '18%',
            left: '8%',
            background: 'rgba(15, 23, 42, 0.90)',
            borderLeft: '8px solid #38BDF8',
            padding: '28px 40px',
            borderRadius: '12px',
            transform: `scale(${statProgress}) translateY(${(1 - statProgress) * 20}px)`,
            opacity: statProgress,
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)'
          }}
        >
          <div
            style={{
              color: '#94A3B8',
              fontSize: '22px',
              fontWeight: 700,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              fontFamily: 'Inter, sans-serif'
            }}
          >
            {scene.visual_overlay.headline || 'CRITICAL METRIC'}
          </div>
          <div
            style={{
              color: '#F8FAFC',
              fontSize: '72px',
              fontWeight: 900,
              marginTop: '6px',
              fontFamily: 'Inter, sans-serif'
            }}
          >
            {scene.visual_overlay.stat_callout}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// Root Composition
export const MainVideo: React.FC<VideoProps> = ({
  scenes,
  words,
  audioUrl,
  bgMusicUrl,
  bgMusicVolume = 0.12
}) => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000000' }}>
      <Series>
        {scenes.map(scene => (
          <Series.Sequence
            key={scene.scene_id}
            durationInFrames={scene.durationInFrames}
          >
            <SceneItem scene={scene} />
          </Series.Sequence>
        ))}
      </Series>

      {words && words.length > 0 && <SubtitlesOverlay words={words} />}
      {audioUrl && <Audio src={resolveMediaSrc(audioUrl)} volume={1.0} />}
      {bgMusicUrl && <Audio src={resolveMediaSrc(bgMusicUrl)} volume={bgMusicVolume} loop />}
    </AbsoluteFill>
  );
};
