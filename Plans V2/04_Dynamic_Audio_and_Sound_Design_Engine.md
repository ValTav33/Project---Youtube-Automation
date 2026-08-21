# 04_Dynamic_Audio_and_Sound_Design_Engine.md

**Objective:**  
Produce licensed, intelligible, dynamically mixed music and sound design synchronized to story structure and narration.

**Dependencies:**

- Exact timing map.
- Scene and shot plan.
- Licensed music and SFX catalog.
- Configurable audio-processing toolchain.

## Phase 1: Build the Audio Catalog

*Make selection, licensing, and reuse programmatic.*

- Create catalog records for every music track:
  - Track ID.
  - File location.
  - Mood.
  - Intensity range.
  - BPM where known.
  - Loop points.
  - Intro and outro suitability.
  - License.
  - Attribution requirements.
- Create SFX categories:
  - Impact.
  - Riser.
  - Whoosh.
  - UI.
  - Mechanical.
  - Financial.
  - Technology.
  - News.
  - Atmosphere.
- Store duration, loudness metadata, and license for every SFX asset.
- Reject unlicensed audio from production manifests.

## Phase 2: Implement the Audio Planner

*Create an emotional soundtrack arc rather than assigning isolated scene tracks.*

- Implement `src/audio_director.py`.
- Divide the story into music sections.
- Assign:
  - Mood.
  - Starting intensity.
  - Ending intensity.
  - Build, hold, release, or resolve action.
  - Preferred track or track category.
- Preserve musical continuity across related scenes.
- Add SFX only to editorially important cues.
- Establish cue-density limits per section.
- Prevent repetitive use of the same impact or whoosh.
- Allow explicit `none` decisions when silence is more effective.

## Phase 3: Compile Audio Cues to Exact Timing

*Translate creative audio intent into a deterministic event list.*

- Anchor reveals and impacts to exact word indexes.
- Convert cue timestamps to frames and audio sample positions.
- Generate:
  - Track start/end.
  - Loop regions.
  - Crossfades.
  - Volume automation.
  - Ducking envelopes.
  - SFX positions.
- Validate that cues do not overlap excessively.
- Shift or remove cues that obscure important narration.
- Add fallback behavior when a word anchor is unavailable.

## Phase 4: Implement the Mixer

*Prioritize narration intelligibility and repeatable output.*

- Normalize narration to a configurable target.
- Apply:
  - Music ducking under speech.
  - Fade-in and fade-out envelopes.
  - Crossfades between tracks.
  - SFX gain limits.
  - True-peak protection.
- Produce separate stems for:
  - Narration.
  - Music.
  - SFX.
  - Final mix.
- Prefer a deterministic FFmpeg-based mix step when it is more reliable than managing many overlapping Remotion audio elements.
- Preserve the original narration file and timestamps.
- Generate a mix report listing loudness, peaks, silence spans, and selected tracks.

## Phase 5: Add Word-Synchronized Audio and Visual Events

*Coordinate sound and motion through shared cue IDs.*

- Give each impact cue a stable `cue_id`.
- Reference the same cue from:
  - Audio plan.
  - Typography animation.
  - Chart movement.
  - Camera change.
- Verify audio and visual cue positions agree within the configured frame tolerance.
- Allow slight visual anticipation where the style profile permits it.
- Add a preview mode that displays cue markers and labels.

## Phase 6: Audio Quality Assurance

*Detect technical and editorial audio problems before final rendering.*

- Check for:
  - Clipping.
  - Missing files.
  - Excessive silence.
  - Abrupt cuts.
  - Overlapping impacts.
  - Unlicensed assets.
  - Music masking narration.
- Generate a reduced-length audio preview for review.
- Test on headphones, laptop speakers, and phone speakers.
- Store human approval notes for mix-profile calibration.
- Version audio-mixing configuration independently from the scene plan.

**Acceptance Criteria:**

- Every production audio asset has recorded license metadata.
- Narration remains intelligible throughout the video.
- Audio and visual impacts share stable synchronized cues.
- The final mix contains no clipping or missing sections.
- The same audio plan produces repeatable output.
