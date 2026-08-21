# 02_Scene_Director_and_Timing_Compiler.md

**Objective:**  
Convert story beats into an executable visual and audio blueprint while maintaining exact synchronization with the generated narration.

**Dependencies:**

- Versioned `StoryScript`.
- ElevenLabs word timestamps.
- Shared Python and TypeScript schemas.
- Initial Remotion component list.

## Phase 1: Define the Editorial Hierarchy

*Prevent story, visual, and timing concepts from being conflated.*

- Define:
  - `StoryBeat`
  - `Scene`
  - `Shot`
  - `Cue`
- Allow one story beat to contain multiple scenes or shots.
- Give each shot:
  - Stable ID.
  - Parent beat ID.
  - Visual purpose.
  - Component.
  - Asset requirements.
  - Start and end anchors.
  - Camera treatment.
  - Caption treatment.
  - Transition.
- Give each cue:
  - Cue type.
  - Word anchor.
  - Frame.
  - Duration.
  - Intensity.
- Add a `style_profile_id` to prevent inconsistent model-generated styling.

## Phase 2: Build the Pre-Voice Intent Planner

*Select creative direction without pretending exact timing is known.*

- Implement `src/scene_director.py`.
- For every story beat, determine:
  - Primary visual objective.
  - Preferred visual type.
  - Fallback visual type.
  - Suggested Remotion component.
  - Caption mode.
  - Emotional intensity.
  - Camera intention.
  - Music intention.
  - SFX opportunities.
- Add continuity constraints:
  - Avoid repeating the same component excessively.
  - Preserve geographic and timeline continuity.
  - Do not switch media merely to satisfy a timer.
  - Reserve impact typography for high-value moments.
- Attach claim references to charts, statistics, and documents.
- Emit an intent plan with estimated timing only.

## Phase 3: Compile Exact Voice Timing

*Map generated narration back to beats and stable word positions.*

- Implement `src/timing_compiler.py`.
- Preserve normalized character offsets when assembling the TTS input.
- Map ElevenLabs word timestamps back to:
  - Beat IDs.
  - Sentence IDs.
  - Claim IDs.
  - Emphasized phrases.
- Normalize:
  - Smart punctuation.
  - Currency formatting.
  - Number pronunciation.
  - Hyphenated words.
  - Quotes and apostrophes.
- Detect mismatches between expected and returned narration.
- Implement fallback alignment using normalized token sequences.
- Stop the pipeline if a critical beat cannot be aligned reliably.
- Convert timestamps into frame positions using the composition frame rate.

## Phase 4: Generate the Shot Plan

*Create variable visual pacing without altering narration timing.*

- Split longer beats at:
  - Sentence boundaries.
  - Clause boundaries.
  - Reveals.
  - Numerical claims.
  - Emotional changes.
- Use pacing profiles:
  - `HIGH_INTENSITY`
  - `EXPLANATORY`
  - `REVEAL`
  - `EMOTIONAL`
  - `RESOLUTION`
- Allow several short shots during a longer narrative beat.
- Enforce configurable:
  - Minimum shot duration.
  - Maximum static hold.
  - Maximum repeated component count.
  - Maximum transition density.
- Anchor important visual events to exact word indexes.
- Use hard cuts by default and reserve expressive transitions for meaningful changes.

## Phase 5: Upgrade Asset Planning and Resolution

*Resolve assets from explicit requirements rather than a single visual prompt.*

- Implement `src/asset_planner.py`.
- For each asset-backed shot, generate several search candidates.
- Specify:
  - Media type.
  - Aspect ratio.
  - Minimum resolution.
  - Required subject.
  - Required action.
  - Time period.
  - Geographic context.
  - Disallowed content.
- Rank Pexels results for semantic and technical fit.
- Use fallback hierarchy:
  1. Existing approved asset cache.
  2. Stock footage.
  3. Stock image.
  4. Document or screenshot.
  5. Data visualization.
  6. AI-generated image.
  7. Typography fallback.
- Do not use AI generation automatically for real people or sensitive historical events without an editorial policy.
- Store every candidate and selection reason.
- Record license and provenance metadata.

## Phase 6: Produce the Renderer Manifest

*Give Remotion a deterministic timeline rather than creative responsibility.*

- Combine:
  - Timing map.
  - Shot plan.
  - Asset manifest.
  - Caption cues.
  - Music cues.
  - SFX cues.
- Validate that:
  - Every frame is covered.
  - Shots do not overlap unintentionally.
  - Required assets exist.
  - Components support the requested props.
  - Every statistic has a claim reference.
- Generate a human-readable storyboard report.
- Generate a machine-readable `renderer_manifest.json`.
- Add a command for rendering a single beat or shot for debugging.

**Acceptance Criteria:**

- Every narration word belongs to a known beat.
- Every shot has valid frame boundaries.
- No shot depends on an unsupported component.
- Required assets have fallbacks and provenance.
- Remotion receives no unresolved creative instructions.
