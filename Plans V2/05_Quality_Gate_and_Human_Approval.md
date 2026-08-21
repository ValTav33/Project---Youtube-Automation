# 05_Quality_Gate_and_Human_Approval.md

**Objective:**  
Prevent weak, invalid, misleading, or technically broken projects from reaching final rendering or public publication.

**Dependencies:**

- Versioned artifacts.
- Preview-render profile.
- Telegram approval interface.
- Quality schemas and stage reports.

## Phase 1: Define the Quality Model

*Replace one opaque score with evidence-backed gates.*

- Define hard blockers:
  - Invalid artifact schema.
  - Unsupported critical claim.
  - Missing narration.
  - Missing required asset.
  - Unlicensed production asset.
  - Invalid shot timing.
  - Missing payoff.
  - Failed render.
- Define warnings:
  - Weak hook.
  - Repetitive visual treatment.
  - Long exposition span.
  - Excessive caption density.
  - Excessive SFX density.
  - Low-confidence asset relevance.
- Keep category scores for diagnostics, but do not use a single uncalibrated number as the only decision.
- Require each finding to include:
  - Artifact ID.
  - Beat or shot ID.
  - Evidence.
  - Suggested correction.
  - Severity.
  - Confidence.

## Phase 2: Add Stage-Specific Preflight Checks

*Catch errors as early as possible.*

- Before TTS:
  - Validate script length.
  - Validate claim references.
  - Check open-loop resolution.
  - Check promise alignment.
- Before asset resolution:
  - Validate component support.
  - Validate data requirements.
  - Validate search requirements.
- Before preview rendering:
  - Validate all timeline ranges.
  - Confirm asset accessibility.
  - Confirm audio-plan completeness.
- Before final rendering:
  - Confirm preview approval.
  - Confirm no unresolved blockers.
  - Confirm configuration and artifact versions.

## Phase 3: Implement Rough-Cut Auditing

*Use actual preview output for findings that cannot be judged from JSON.*

- Render a low-resolution preview.
- Extract:
  - Contact-sheet frames.
  - Shot boundaries.
  - Caption frames.
  - Audio report.
- Detect:
  - Black or empty frames.
  - Frozen assets.
  - Incorrect crops.
  - Caption overflow.
  - Repeated visuals.
  - Abrupt audio transitions.
  - Unintended silence.
- Run a rough-cut retention audit using exact timestamps.
- Identify weak intervals by beat and shot ID rather than returning only free-form comments.

## Phase 4: Implement Targeted Regeneration

*Repair the smallest possible artifact.*

- Map each finding to an allowed action:
  - Rewrite beat.
  - Replace asset.
  - Change component.
  - Split shot.
  - Simplify caption.
  - Change music cue.
  - Rebuild thumbnail.
- Preserve approved facts and unaffected artifacts.
- Increment the revision only for changed artifacts.
- Limit regeneration attempts by category.
- Require human review after the retry limit.
- Store before-and-after diffs.

## Phase 5: Extend Telegram into a Real Approval Console

*Add editorial and publication decisions after generation.*

- Add Telegram actions for:
  - Approve script.
  - Request script revision.
  - Approve preview.
  - Regenerate selected section.
  - Approve title.
  - Approve thumbnail.
  - Approve publication.
  - Reject project.
- Upload previews to a private storage location with signed access, or upload them privately to YouTube.
- Add statuses:
  - `awaiting_script_approval`
  - `awaiting_preview_approval`
  - `awaiting_publish_approval`
- Display blockers and warnings in concise Telegram summaries.
- Record approver identity, timestamp, artifact revision, and notes.
- Make publication approval configurable for trusted unattended operation, but enabled by default during rollout.

## Phase 6: Calibrate Quality Decisions

*Improve evaluator reliability using real human decisions.*

- Compare model findings with human review notes.
- Track false positives and missed problems.
- Adjust thresholds by content category.
- Version all evaluator prompts and rule configurations.
- Do not silently change quality policy for in-progress projects.
- Publish periodic reports on:
  - Most common blockers.
  - Most regenerated component types.
  - Average revision count.
  - Preview rejection reasons.

**Acceptance Criteria:**

- Hard blockers stop progression automatically.
- Exact-time rough-cut findings are based on rendered output.
- Regeneration can target individual beats, shots, assets, or cues.
- Public publication has a recorded approval when the gate is active.
- Quality decisions remain traceable to evidence and evaluator versions.
