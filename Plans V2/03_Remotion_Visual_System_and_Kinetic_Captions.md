# 03_Remotion_Visual_System_and_Kinetic_Captions.md

**Objective:**  
Create a reusable, typed, cinematic Remotion component system with semantic captions, visual variety, safe fallbacks, and testable behavior.

**Dependencies:**

- `renderer_manifest.json`
- Shared Zod schemas.
- Style profile and design tokens.
- Representative test assets.

## Phase 1: Establish the Visual Design System

*Define one coherent channel language before adding many components.*

- Define:
  - Font families and weights.
  - Color palette.
  - Caption colors.
  - Chart colors.
  - Spacing scale.
  - Border and shadow styles.
  - Safe areas.
  - Transition durations.
  - Camera movement presets.
- Create an original style profile based on high-level traits such as investigative, cinematic, restrained, and data-rich.
- Define motion-intensity levels.
- Establish limits on glow, blur, shake, and impact effects.
- Create a design-preview composition showing every token.

## Phase 2: Build the Component Runtime

*Make all renderer choices pass through a safe registry.*

- Create a component registry:

```ts
const componentRegistry = {
  CinematicMedia,
  FullScreenTypography,
  BigNumber,
  StatCard,
  Chart,
  Timeline,
  QuoteCard,
  DocumentCard,
};
```

- Define shared component props:
  - Frame range.
  - Content.
  - Asset.
  - Entry and exit motion.
  - Camera treatment.
  - Caption behavior.
  - Source label.
- Add schema validation before component selection.
- Create an `UnsupportedDirective` fallback component.
- Add React error boundaries around shot rendering.
- Preload remote assets and detect failures before final rendering.
- Keep all frame calculations deterministic.

## Phase 3: Implement the Core Component Set

*Prioritize the components that provide the greatest immediate visual improvement.*

- Implement `CinematicMedia`:
  - Images and video.
  - Crop and focal point.
  - Push-in, pull-out, pan, and static modes.
- Implement `FullScreenTypography`:
  - Word and phrase layouts.
  - Impact and restrained modes.
- Implement `BigNumber`:
  - Count-up/down.
  - Currency and percentage formatting.
  - Optional comparison context.
- Implement `StatCard`:
  - Label, value, source, and trend.
- Implement `Chart`:
  - Bar, line, and area modes.
  - Progressive reveal.
  - Highlighted data points.
- Implement `Timeline`:
  - Ordered events.
  - Current-event focus.
- Implement `QuoteCard`:
  - Speaker, quote, source, and date.
- Implement `DocumentCard`:
  - Screenshot crop.
  - Highlight box.
  - Redaction and blur controls.
- Add split-screen, map, comparison, and newspaper components only after the core set is stable.

## Phase 4: Implement Semantic Kinetic Captions

*Combine readable captions with selective emphasis.*

- Parse exact word timestamps into phrase groups.
- Keep phrase boundaries aligned with:
  - Punctuation.
  - Natural pauses.
  - Maximum line length.
  - Maximum on-screen word count.
- Map emphasis using word indexes rather than raw string search.
- Implement:
  - `NORMAL`
  - `EMPHASIS`
  - `IMPACT`
  - `QUOTE`
  - `STATISTIC`
- Keep normal captions visually restrained.
- Use impact typography only when explicitly directed.
- Add automatic text fitting and overflow detection.
- Enforce title-safe and caption-safe areas.
- Provide high-contrast fallback styling for bright footage.
- Allow captions to be disabled for title cards and document-heavy shots.

## Phase 5: Implement Controlled Visual Variety

*Prevent monotony without producing random edits.*

- Track the recent component sequence.
- Warn when:
  - The same component repeats too frequently.
  - Stock footage dominates an entire section.
  - Too many typography scenes appear consecutively.
- Apply transitions according to narrative purpose:
  - Hard cut for pace.
  - Dissolve for passage of time.
  - Match cut for comparisons.
  - Dip or fade for chapter changes.
- Create pattern interrupts only at semantic boundaries.
- Add chapter-card support for major story acts.
- Use source labels consistently on statistics and documents.

## Phase 6: Add Renderer Testing and Performance Controls

*Make component expansion safe and repeatable.*

- Create a visual gallery composition containing valid and edge-case examples.
- Add tests for:
  - Long titles.
  - Large currency values.
  - Missing assets.
  - Portrait assets.
  - Low-resolution images.
  - Empty chart series.
  - Caption overflow.
  - Non-ASCII text.
- Render short frame ranges in CI or local test automation.
- Compare selected reference frames against approved snapshots.
- Measure render time and memory per component.
- Cache downloaded media.
- Add a low-resolution preview render profile.

**Acceptance Criteria:**

- Invalid component props fail before rendering.
- Every component has a defined fallback.
- Captions remain inside safe areas and do not overflow.
- The same manifest produces deterministic frame output.
- A component gallery can be reviewed without running the full pipeline.
