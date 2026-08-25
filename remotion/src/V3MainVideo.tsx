import React from 'react';
import { Sequence, Audio } from 'remotion';
import { CinematicMedia } from './components/v3/CinematicMedia';
import { EvidenceCard } from './components/v3/EvidenceCard';
import { BigNumber } from './components/v3/BigNumber';
import { DataChart } from './components/v3/DataChart';
import { Timeline } from './components/v3/Timeline';
import { Comparison } from './components/v3/Comparison';
import { ProductScreen } from './components/v3/ProductScreen';
import { TypographyImpact } from './components/v3/TypographyImpact';

// This matches the Python ProductionManifest Pydantic schema
export interface V3ProductionManifestProps {
  manifest: {
    fps: number;
    width: number;
    height: number;
    total_frames: number;
    shots: {
      shot_id: string;
      start_frame: number;
      duration_frames: number;
      component_type: string;
      component_props: any;
      asset_url?: string;
    }[];
    audio_tracks?: {
      track_id: string;
      audio_type: string;
      asset_url: string;
      start_frame: number;
      duration_frames: number;
      volume: number;
    }[];
  }
}

export const V3MainVideo: React.FC<V3ProductionManifestProps> = ({ manifest }) => {
  return (
    <>
      {manifest.shots.map((shot) => {
        let Component;
        switch (shot.component_type) {
          case 'CinematicMedia': Component = CinematicMedia; break;
          case 'EvidenceCard': Component = EvidenceCard; break;
          case 'BigNumber': Component = BigNumber; break;
          case 'DataChart': Component = DataChart; break;
          case 'Timeline': Component = Timeline; break;
          case 'Comparison': Component = Comparison; break;
          case 'ProductScreen': Component = ProductScreen; break;
          case 'TypographyImpact': Component = TypographyImpact; break;
          default: Component = CinematicMedia;
        }

        return (
          <Sequence key={shot.shot_id} from={shot.start_frame} durationInFrames={shot.duration_frames}>
            <Component {...shot.component_props} assetUrl={shot.asset_url} />
          </Sequence>
        );
      })}
      {manifest.audio_tracks?.map((track) => (
        <Sequence key={track.track_id} from={track.start_frame} durationInFrames={track.duration_frames}>
          <Audio src={track.asset_url} volume={track.volume} />
        </Sequence>
      ))}
    </>
  );
};
