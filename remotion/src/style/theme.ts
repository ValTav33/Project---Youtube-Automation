import { spring } from 'remotion';

// V3 Deep Dark Mode Aesthetic
export const Theme = {
  colors: {
    background: '#0F172A', // Slate 900
    surface: '#1E293B', // Slate 800
    surfaceHighlight: '#334155', // Slate 700
    textPrimary: '#F8FAFC', // Slate 50
    textSecondary: '#94A3B8', // Slate 400
    accent: '#0EA5E9', // Sky 500 (Electric Blue)
    accentHighlight: '#38BDF8', // Sky 400
    danger: '#EF4444', // Red 500
    success: '#10B981', // Emerald 500
  },
  fonts: {
    primary: '"Inter", sans-serif',
    display: '"Outfit", "Inter", sans-serif',
    mono: '"Fira Code", monospace',
  },
  typography: {
    title: { fontSize: 84, fontWeight: 800, lineHeight: 1.1, letterSpacing: '-0.02em' },
    headline: { fontSize: 64, fontWeight: 700, lineHeight: 1.2, letterSpacing: '-0.01em' },
    body: { fontSize: 36, fontWeight: 400, lineHeight: 1.5, letterSpacing: '0' },
    caption: { fontSize: 24, fontWeight: 500, lineHeight: 1.4, letterSpacing: '0.05em', textTransform: 'uppercase' },
  },
  layout: {
    padding: 80,
    borderRadius: 24,
    gap: 40,
  }
};

export const Motion = {
  springs: {
    smooth: (frame: number, fps: number) => spring({ frame, fps, config: { damping: 20, stiffness: 120, mass: 1 } }),
    snappy: (frame: number, fps: number) => spring({ frame, fps, config: { damping: 15, stiffness: 200, mass: 0.8 } }),
    bouncy: (frame: number, fps: number) => spring({ frame, fps, config: { damping: 10, stiffness: 150, mass: 1 } }),
  }
};
