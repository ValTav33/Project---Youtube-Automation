import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';

interface WordTimestamp {
  word: string;
  start: number;
  end: number;
}

export const Subtitles: React.FC<{ words: WordTimestamp[] }> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  // Find all words that should be visible (e.g., standard shorts style shows the current word with some context)
  // Let's implement a simple style: show the active word in the center.
  
  const currentWord = words.find(w => currentTime >= w.start && currentTime <= w.end);

  if (!currentWord) {
    return null;
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: '300px', // slightly below center to leave room for the main subject
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          padding: '20px 40px',
          borderRadius: '20px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
        }}
      >
        <h1
          style={{
            fontFamily: 'system-ui, sans-serif',
            fontSize: '80px',
            color: 'white',
            margin: 0,
            textTransform: 'uppercase',
            fontWeight: 'bold',
            textShadow: '0 4px 10px rgba(0,0,0,0.8)',
            textAlign: 'center',
          }}
        >
          {currentWord.word}
        </h1>
      </div>
    </AbsoluteFill>
  );
};
