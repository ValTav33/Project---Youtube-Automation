# 06_Title_Thumbnail_and_Publish_Package.md

**Objective:**  
Make the title, thumbnail, hook, opening, and final payoff parts of one coherent viewer promise and introduce controlled metadata experimentation.

**Dependencies:**

- Promise Contract.
- Final or approved script.
- Approved preview.
- Thumbnail generation provider.
- Publication approval workflow.

## Phase 1: Define the Publish Package

*Create a versioned artifact instead of generating metadata immediately before upload.*

- Include:
  - Selected title.
  - Alternate titles.
  - Thumbnail variants.
  - Description.
  - Tags.
  - Chapters.
  - Privacy setting.
  - Schedule.
  - Promise Contract reference.
  - Script revision.
  - Preview revision.
- Validate platform length and formatting constraints.
- Store the package before invoking the YouTube API.
- Require package approval independently from preview approval.

## Phase 2: Align Title and Thumbnail with the Story

*Ensure the video fulfills what the packaging promises.*

- Extract the title’s primary claim.
- Verify that the claim:
  - Appears in the hook.
  - Is supported by the Research Packet.
  - Receives a clear payoff.
- Reject thumbnails containing unsupported numbers or implications.
- Generate thumbnail concepts from the Promise Contract rather than only the final title.
- Preserve text-free and low-text variants where appropriate.
- Add a mobile-size legibility preview.

## Phase 3: Generate and Rank Variants

*Create options without pretending model scoring is equivalent to CTR.*

- Generate several distinct concepts, not minor wording changes.
- Classify title strategy:
  - Outcome.
  - Mystery.
  - Contradiction.
  - Transformation.
  - Failure.
- Classify thumbnail strategy:
  - Number transformation.
  - Before/after.
  - Central object.
  - Human expression where appropriate.
  - Document or evidence.
- Score for clarity, truthfulness, legibility, and title complementarity.
- Keep human selection during the initial deployment.

## Phase 4: Make Publishing Safe and Idempotent

*Prevent duplicate or accidental public uploads.*

- Use a publication idempotency key.
- Save resumable-upload state.
- Default initial uploads to private during rollout.
- Change privacy or schedule only after approval.
- Store YouTube video ID immediately after upload creation.
- Treat thumbnail upload and metadata updates as retryable independent stages.
- Prevent reruns from creating a second video when an existing YouTube ID is known.

## Phase 5: Prepare for Experiments

*Record variants and exposure without prematurely automating decisions.*

- Assign an experiment ID to each packaging test.
- Store every title and thumbnail variant.
- Record:
  - Selected variant.
  - Activation time.
  - Replacement time.
  - Reason for change.
- Change one major packaging variable at a time where practical.
- Feed experiment metadata into the analytics system.
- Require minimum exposure before declaring a winner.

**Acceptance Criteria:**

- Every published title and thumbnail is linked to a Promise Contract.
- Unsupported packaging claims are blocked.
- Publication reruns do not create duplicate YouTube videos.
- All variants and changes are versioned and auditable.
