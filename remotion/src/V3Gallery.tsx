import React from 'react';
import { Sequence } from 'remotion';
import { CinematicMedia } from './components/v3/CinematicMedia';
import { EvidenceCard } from './components/v3/EvidenceCard';
import { BigNumber } from './components/v3/BigNumber';
import { DataChart } from './components/v3/DataChart';
import { Timeline } from './components/v3/Timeline';
import { Comparison } from './components/v3/Comparison';
import { ProductScreen } from './components/v3/ProductScreen';
import { TypographyImpact } from './components/v3/TypographyImpact';

export const V3Gallery: React.FC = () => {
  const FPS = 30;
  const SHOT_DURATION = 3 * FPS; // 3 seconds per component

  return (
    <>
      <Sequence from={0} durationInFrames={SHOT_DURATION}>
        <CinematicMedia />
      </Sequence>

      <Sequence from={SHOT_DURATION} durationInFrames={SHOT_DURATION}>
        <EvidenceCard primaryText="Over 80% of projects fail due to poor scoping." secondaryText="Harvard Business Review" />
      </Sequence>

      <Sequence from={SHOT_DURATION * 2} durationInFrames={SHOT_DURATION}>
        <BigNumber primaryText="10,000+" secondaryText="Active Users" />
      </Sequence>

      <Sequence from={SHOT_DURATION * 3} durationInFrames={SHOT_DURATION}>
        <DataChart primaryText="Quarterly Growth" />
      </Sequence>

      <Sequence from={SHOT_DURATION * 4} durationInFrames={SHOT_DURATION}>
        <Timeline primaryText="V3 Architecture Proposed" secondaryText="August 2026" />
      </Sequence>

      <Sequence from={SHOT_DURATION * 5} durationInFrames={SHOT_DURATION}>
        <Comparison primaryText="Legacy System" secondaryText="V3 Pipeline" />
      </Sequence>

      <Sequence from={SHOT_DURATION * 6} durationInFrames={SHOT_DURATION}>
        <ProductScreen primaryText="The New Interface" />
      </Sequence>

      <Sequence from={SHOT_DURATION * 7} durationInFrames={SHOT_DURATION}>
        <TypographyImpact primaryText="THE END" />
      </Sequence>
    </>
  );
};
