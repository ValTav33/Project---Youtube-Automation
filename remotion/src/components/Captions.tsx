import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import { WordTimestamp } from '../types';

export const Captions: React.FC<{ words: WordTimestamp[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Current time in seconds
  const currentTime = frame / fps;

  // Find the word currently being spoken
  const currentWordIndex = words.findIndex(
    (w) => currentTime >= w.start && currentTime <= w.end
  );

  if (currentWordIndex === -1) {
    return null;
  }

  // To create a "Kinetic" semantic caption feel, we show a small chunk of words (e.g. 5 words)
  // centered around the current word, highlighting the current word in a distinct color.
  const windowSize = 2; // words before and after
  const startIndex = Math.max(0, currentWordIndex - windowSize);
  const endIndex = Math.min(words.length - 1, currentWordIndex + windowSize + 1); // +1 for looking ahead slightly
  
  const visibleWords = words.slice(startIndex, endIndex);

  return (
    <div style={{
      position: 'absolute',
      bottom: '10%',
      left: '10%',
      right: '10%',
      display: 'flex',
      flexWrap: 'wrap',
      justifyContent: 'center',
      alignItems: 'center',
      gap: '12px',
      textShadow: '0px 4px 12px rgba(0,0,0,0.8)',
      pointerEvents: 'none' // Don't block interactions if any
    }}>
      {visibleWords.map((w, idx) => {
        const isCurrent = w.start <= currentTime && w.end >= currentTime;
        return (
          <span 
            key={idx} 
            style={{
              fontSize: isCurrent ? '72px' : '64px',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              fontWeight: '900',
              color: isCurrent ? '#facc15' : 'white',
              opacity: isCurrent ? 1 : 0.8,
              transition: 'all 0.1s ease-out',
              textTransform: 'uppercase'
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};
