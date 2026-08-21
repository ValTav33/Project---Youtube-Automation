# 00_Pipeline_Contracts_and_Workflow_Foundation.md

**Objective:**  
Introduce the data contracts, versioning, stage management, validation, and operational safeguards required by the retention, directing, audio, quality, and analytics systems without replacing the existing Supabase/local architecture.

**Dependencies:**

- Access to the current Python and Remotion repositories.
- A staging Supabase project.
- A test Telegram bot or isolated test chat.
- Test credentials or API mocks for OpenAI, ElevenLabs, Pexels, Fal.ai, and YouTube.

## Phase 1: Establish the Current Baseline

*Document actual behavior before modifying the pipeline.*

- Trace `run_pipeline_for_video(video_id)` through every imported module.
- Document:
  - Inputs and outputs of each function.
  - Supabase reads and writes.
  - Storage bucket access.
  - Environment variables.
  - Retry behavior.
  - Failure behavior.
  - Local file creation.
- Capture one completed project as a golden fixture:
  - Original database row.
  - Generated script.
  - Voice timestamps.
  - Resolved assets.
  - Remotion props.
  - Rendered video.
  - Thumbnail and publication metadata.
- Create a pipeline smoke test using mocked third-party responses.
- Identify undocumented assumptions, including public storage URLs, fixed local paths, and hard-coded frame rates.

## Phase 2: Define Shared Artifact Contracts

*Create one authoritative schema for every pipeline artifact.*

- Define JSON Schemas for:
  - `PromiseContract`
  - `ResearchPacket`
  - `StoryScript`
  - `SceneIntentPlan`
  - `TimingMap`
  - `ShotPlan`
  - `AssetManifest`
  - `AudioPlan`
  - `QualityReport`
  - `PublishPackage`
  - `AnalyticsFeatureVector`
- Add the following common fields:
  - `artifact_id`
  - `video_id`
  - `artifact_type`
  - `schema_version`
  - `revision`
  - `parent_artifact_ids`
  - `input_hash`
  - `created_at`
  - `created_by`
- Generate or manually maintain:
  - Pydantic models for Python.
  - Zod schemas and TypeScript types for Remotion.
- Reject unknown component names and invalid enum values before rendering.
- Add migration handlers so old `script_payload` records can still render during transition.

## Phase 3: Evolve the Supabase Data Model

*Keep `videos` as the project summary while moving detailed artifacts out of the mutable payload.*

- Add an `artifacts` table for versioned JSON and file-backed outputs.
- Add a `pipeline_runs` table containing:
  - Stage.
  - Attempt number.
  - Status.
  - Input and output artifact IDs.
  - Start/end timestamps.
  - Error classification.
  - API cost estimate.
- Add a `pipeline_events` table for append-only progress and diagnostic events.
- Add an `approvals` table for topic, script, preview, and publication decisions.
- Add an `assets` table containing:
  - Provider.
  - Source URL.
  - Storage URL.
  - Media type.
  - Dimensions and duration.
  - License metadata.
  - Checksum.
- Retain summary fields in `videos`, but stop storing render progress and resolved assets inside the script.
- Backfill existing records into version-one artifacts.
- Create database constraints for allowed stage transitions.

## Phase 4: Implement a Resumable Stage Runner

*Replace ad hoc sequential mutation with explicit, idempotent stages.*

- Create a common stage interface:

```python
class PipelineStage:
    name: str
    input_types: list[str]
    output_type: str

    def validate_inputs(self, context): ...
    def execute(self, context): ...
    def validate_output(self, artifact): ...
```

- Assign every stage an idempotency key based on:
  - Video ID.
  - Stage name.
  - Input artifact hashes.
  - Configuration version.
- Add a database lease or advisory lock so two orchestrators cannot process the same video.
- Save stage outputs before changing the project’s summary status.
- Classify failures as:
  - Retryable API failure.
  - Invalid model output.
  - Missing asset.
  - Configuration failure.
  - Human-review requirement.
  - Fatal rendering failure.
- Add bounded retries with backoff.
- Support `resume`, `retry-stage`, and `restart-from-stage` commands.
- Record external API request IDs when providers expose them.

## Phase 5: Add Security and Operational Controls

*Protect unpublished assets, credentials, and production state.*

- Replace public unpublished media URLs with signed or private URLs where practical.
- Review Supabase RLS policies for all project, artifact, and approval tables.
- Store Railway secrets in Railway’s secret management rather than committed files.
- Protect local OAuth files with restrictive filesystem permissions.
- Redact API keys, signed URLs, and OAuth tokens from logs.
- Add per-video and per-stage cost ceilings.
- Stop regeneration when a configured budget or attempt limit is reached.
- Add structured logs containing `video_id`, `run_id`, `stage`, and `artifact_id`.

## Phase 6: Compatibility Rollout

*Introduce the new workflow without interrupting existing production.*

- Add a feature flag for artifact-based execution.
- Run old and new schema generation in shadow mode for several test projects.
- Compare final props and outputs.
- Migrate one noncritical video through the new runner.
- Document rollback steps.
- Remove writes to the legacy mutable fields only after successful validation.

**Acceptance Criteria:**

- A failed run can resume without repeating completed billable stages.
- All stage inputs and outputs pass shared Python and TypeScript validation.
- Creative artifacts are independently versioned.
- Duplicate orchestrators cannot process the same project simultaneously.
- No public publication can occur without a recorded approval when the gate is enabled.
