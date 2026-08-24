import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';
import { Theme, Motion } from '../../style/theme';

interface DataChartProps {
  primaryText?: string;
}

export const DataChart: React.FC<DataChartProps> = ({ 
  primaryText = 'Data Trend' 
}) => {
  const frame = useCurrentFrame();
  
  // Dummy data for visual representation
  const dataPoints = [30, 45, 60, 40, 80, 95, 120];
  const maxVal = Math.max(...dataPoints);

  return (
    <AbsoluteFill style={{ 
      backgroundColor: Theme.colors.background,
      display: 'flex',
      flexDirection: 'column',
      padding: Theme.layout.padding * 1.5
    }}>
      <h2 style={{
        ...Theme.typography.headline,
        color: Theme.colors.textPrimary,
        marginBottom: 80
      }}>
        {primaryText}
      </h2>

      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'flex-end',
        gap: 20,
        borderBottom: `2px solid ${Theme.colors.surfaceHighlight}`,
        borderLeft: `2px solid ${Theme.colors.surfaceHighlight}`,
        padding: '20px 0 0 20px'
      }}>
        {dataPoints.map((val, i) => {
          // Stagger the animation of each bar
          const delay = i * 5;
          const barHeightSpring = Motion.springs.snappy(Math.max(0, frame - delay), 30);
          const heightPct = (val / maxVal) * 100 * barHeightSpring;

          return (
            <div key={i} style={{
              flex: 1,
              height: `${heightPct}%`,
              backgroundColor: i === dataPoints.length - 1 ? Theme.colors.accent : Theme.colors.surfaceHighlight,
              borderTopLeftRadius: 8,
              borderTopRightRadius: 8,
              position: 'relative'
            }}>
              {/* Value label on top of bar */}
              <div style={{
                position: 'absolute',
                top: -40,
                width: '100%',
                textAlign: 'center',
                ...Theme.typography.caption,
                color: i === dataPoints.length - 1 ? Theme.colors.accent : Theme.colors.textSecondary,
                opacity: interpolate(barHeightSpring, [0.8, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
              }}>
                {val}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
