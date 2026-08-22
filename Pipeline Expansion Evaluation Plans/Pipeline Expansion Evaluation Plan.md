# Pipeline Expansion Evaluation Plan

## 1. Establish the evaluation baseline

Before testing the new implementation, freeze the expected behavior against which it will be compared.

### 1.1 Document the legacy behavior

Create a baseline document containing:

- Existing pipeline stages.
- Existing status transitions.
- Existing database fields.
- Existing Supabase storage buckets.
- Existing external API calls.
- Existing Remotion props.
- Existing output files.
- Existing error behavior.
- Existing rendering and publishing behavior.

The documented baseline currently shows that state is concentrated in the `videos` row, with the script, resolved assets, transcript timestamps, and render progress stored there. It also identifies hard-coded paths, a hard-coded 30 FPS value, local OAuth files, and the absence of explicit retry or resumability behavior. 

### 1.2 Capture a golden fixture

Select one representative video and preserve:

- Input topic and premise.
- Original `videos` row.
- Generated script.
- Narration text.
- ElevenLabs timestamps.
- Resolved assets.
- Remotion `props.json`.
- Final rendered MP4.
- Thumbnail.
- YouTube metadata, if applicable.
- Logs and error notifications.
- Pipeline duration and API usage.

This fixture becomes the regression reference for the legacy path and, where appropriate, the new path.

### 1.3 Define the target architecture

Create a target-stage checklist based on the intended design:

```text
Topic Intake
  ↓
Promise Contract
  ↓
Research Packet and Claim Ledger
  ↓
Hook / Story / Retention Planning
  ↓
Story Script
  ↓
Scene Intent Plan
  ↓
Voice Generation
  ↓
Timing Map
  ↓
Shot Plan
  ↓
Asset Manifest and Resolution
  ↓
Audio Plan and Mix
  ↓
Preview Render
  ↓
Quality Gate
  ↓
Human Preview Approval
  ↓
Final Render
  ↓
Publish Package Approval
  ↓
YouTube Publication
  ↓
Analytics Instrumentation
```

This ordering is important. Creative visual intent can be planned before voice generation, but exact timing must be compiled after the narration and word timestamps exist. 

---

# 2. Build a traceability matrix

For every implementation series, map the following:

| Requirement | Expected implementation | Evidence required | Test |
|---|---|---|---|
| Versioned artifacts | Artifact schemas, IDs, revisions, hashes | Database rows and schema validation | Contract tests |
| Resumable execution | Stage runner and idempotency keys | `pipeline_runs`, logs | Failure/resume test |
| Scene direction | Intent plan before TTS | `SceneIntentPlan` artifact | Structural test |
| Exact synchronization | Timing compiler after TTS | `TimingMap` artifact | Timestamp alignment test |
| Shot planning | Multiple shots per beat | `ShotPlan` artifact | Timeline invariant test |
| Asset provenance | Candidate and selection metadata | `assets` and manifest records | Rights/provenance test |
| Renderer determinism | Manifest-driven Remotion render | Identical props/manifests | Repeated render test |
| Quality gate | Blockers and warnings | `QualityReport` | Negative test suite |
| Human approval | Script, preview, and publication gates | Approval records | Workflow test |
| Analytics | Frozen creative feature vector | Analytics artifact | Publication instrumentation test |

A feature should not be considered implemented merely because a module or database table exists. It must be traceable from:

**requirement → code → persisted artifact → runtime event → automated test → observable output**.

---

# 3. Verify the data contracts

The expanded architecture requires independent, versioned artifacts such as `StoryScript`, `SceneIntentPlan`, `TimingMap`, `ShotPlan`, `AssetManifest`, `AudioPlan`, `QualityReport`, and `PublishPackage`. The contracts should include fields such as artifact ID, video ID, schema version, revision, parent artifacts, input hash, creator, and timestamp. 

## 3.1 Contract validation tests

For every artifact:

- Validate required fields.
- Reject unknown fields where strict validation is required.
- Validate enum values.
- Validate UUIDs and identifiers.
- Validate references to parent artifacts.
- Validate revision numbers.
- Validate input hashes.
- Validate timestamp formats.
- Validate numeric ranges.
- Validate optional and nullable fields.
- Validate backwards-compatible migration from legacy `script_payload`.

Test both Python-side models and TypeScript/Zod-side models. The Python and Remotion representations must accept and reject the same data.

## 3.2 Cross-artifact consistency tests

Verify that:

- Every artifact references the correct `video_id`.
- Every artifact has the expected parent artifact.
- A `TimingMap` references the correct `StoryScript`.
- A `ShotPlan` references the correct `TimingMap` and `SceneIntentPlan`.
- An `AssetManifest` references the correct shots.
- A `QualityReport` evaluates the exact artifact revisions used for rendering.
- A `PublishPackage` references the approved final render and approved thumbnail.

A critical failure should occur if the renderer receives artifacts from mixed revisions.

## 3.3 Legacy compatibility tests

Use a legacy `videos` row containing only:

- `script_payload`.
- `audio_url`.
- `transcript_timestamps`.
- Legacy scene structure.

Confirm that:

- The migration layer can create version-one artifacts.
- The old render path still works if compatibility mode is enabled.
- The new pipeline does not silently reinterpret old fields incorrectly.
- Rollback to the legacy path is possible.

---

# 4. Verify the stage runner and state machine

The target architecture requires explicit, idempotent stages rather than a sequence of mutable database updates. Each stage should validate its inputs, execute, validate its output, persist the result, and then update summary state. 

## 4.1 Stage-level checks

For every stage, verify:

- It has a unique name.
- It declares input artifact types.
- It declares its output artifact type.
- It validates inputs before making external calls.
- It writes an output artifact before advancing status.
- It validates its own output.
- It records start and end times.
- It records attempt number.
- It records errors using a defined classification.
- It records the input and output artifact IDs.
- It records configuration and model versions.
- It emits structured events containing `video_id`, `run_id`, `stage`, and `artifact_id`.

## 4.2 Idempotency tests

Run the same stage twice with identical inputs and configuration.

Expected result:

- No duplicate billable API calls where caching is possible.
- No duplicate artifacts unless a new revision is explicitly requested.
- No duplicate uploaded media.
- No duplicated publication.
- The same idempotency key produces the same logical result.

The idempotency key should include the video ID, stage name, input artifact hashes, and configuration version. 

## 4.3 Concurrency tests

Start two orchestrators against the same approved video.

Expected result:

- Only one obtains the lease or lock.
- Only one executes the stage.
- The second process exits or waits safely.
- No artifact or database row is corrupted.
- No duplicate render or YouTube upload occurs.

This specifically addresses the baseline concurrency risk caused by repeatedly mutating the same `videos` row and patching render progress into `script_payload`. 

## 4.4 Resume and retry tests

Simulate failure at every major stage:

- Script generation.
- Research generation.
- Voice generation.
- Timing compilation.
- Asset resolution.
- Preview rendering.
- Quality evaluation.
- Final rendering.
- Thumbnail generation.
- YouTube upload.

For each failure, verify:

- The stage is marked failed.
- The failure is correctly classified.
- Completed stages are not unnecessarily repeated.
- `resume` continues from the correct stage.
- `retry-stage` only retries the failed stage.
- `restart-from-stage` invalidates dependent artifacts correctly.
- Retryable errors use bounded backoff.
- Non-retryable errors stop immediately.
- Human-review failures do not automatically retry.

The intended acceptance criterion is that a failed run can resume without repeating completed billable stages. 

---

# 5. Validate the editorial and factual pipeline

The expansion is not only a technical pipeline. It also changes how a video is planned and generated.

## 5.1 Promise Contract

Verify that each project produces a contract containing:

- Viewer question.
- Promise to the viewer.
- Title direction.
- Thumbnail concept.
- Required payoff.
- Topic boundaries.
- Disallowed interpretations.

Test that the final script and publish package remain aligned with the original promise.

## 5.2 Research Packet and claim ledger

Every factual, numerical, historical, or quoted claim should have:

- A stable claim ID.
- Source references.
- Confidence level.
- Approval state.
- Supporting evidence.
- Optional uncertainty or qualification.

Verify that:

- Script claims reference known claims.
- Statistics reference approved sources.
- Charts consume claim data rather than independently generated numbers.
- Timeline events reference source records.
- Document cards identify their source.
- Title and thumbnail claims are traceable.
- Unsupported claims are blocked or routed for human review.

This is especially important because the application is intended to produce data-rich documentary and case-study videos, and the design documents identify factuality and provenance as a major missing layer. 

## 5.3 Story and retention behavior

Test whether the generated story contains the intended structure:

- Hook.
- Viewer promise.
- Open loop.
- Escalation.
- Reveals.
- Consequences.
- Resolution or payoff.

Do not use only an LLM score. Combine:

- Deterministic structural checks.
- Rule-based interval checks.
- Model-assisted editorial evaluation.
- Human review of representative outputs.

The system should report findings by beat or shot, rather than producing only a single overall score.

---

# 6. Validate scene, shot, and timing correctness

The architecture explicitly separates:

- **Story beat** — narrative unit.
- **Scene** — continuous visual treatment.
- **Shot** — short visual unit.
- **Cue** — timed event such as a caption, SFX, transition, or emphasis.

This separation is necessary because 35–45 semantic scenes in an 8–10 minute video cannot all be treated as 2–7 second visual cuts. 

## 6.1 Timing compiler tests

Use synthetic narration fixtures containing:

- Punctuation.
- Smart quotes.
- Apostrophes.
- Hyphenated words.
- Currency.
- Percentages.
- Large numbers.
- Dates.
- Abbreviations.
- Non-ASCII text.
- Repeated words.
- Similar phrases.

Verify that:

- Every narration word maps to a known beat.
- Sentence and claim references are correct.
- Emphasized phrases use word indexes, not fragile string matching.
- Normalization does not change the intended text.
- Mismatches are detected.
- Fallback alignment works when normalization is sufficient.
- Critical alignment failures stop the pipeline.
- Frame conversion uses the configured FPS rather than an untracked hard-coded value.

## 6.2 Timeline invariants

For every generated timing map and shot plan:

- Start frame is less than end frame.
- No negative duration exists.
- No unintended overlaps exist.
- No gaps exist in required coverage.
- The first shot begins at the expected frame.
- The final shot ends at the audio duration.
- All word timestamps fall inside the corresponding beat.
- All shots belong to a valid beat and scene.
- Every important cue has a valid anchor.
- Frame rounding does not create gaps or overlaps.
- The sum of the timeline duration matches the audio duration within the defined tolerance.

## 6.3 Shot pacing tests

Verify configurable rules for:

- Minimum shot duration.
- Maximum static hold.
- Maximum repeated component count.
- Maximum transition density.
- Pacing profile behavior.
- Semantic cut points.
- Reveal timing.
- Numerical claim emphasis.
- First-minute visual pacing.

A shot should not be split merely because a timer expired. Splits should occur at sentence boundaries, clauses, reveals, numerical claims, emotional changes, or other semantically meaningful locations. 

---

# 7. Validate asset planning, resolution, and rights

The expanded system should resolve assets from explicit requirements rather than one visual prompt.

## 7.1 Asset requirement tests

For each asset-backed shot, verify that the plan includes:

- Media type.
- Aspect ratio.
- Minimum resolution.
- Required subject.
- Required action.
- Time period.
- Geographic context.
- Disallowed content.
- Intended visual purpose.
- Fallback type.

## 7.2 Fallback hierarchy tests

Force each provider to fail and verify the expected fallback order:

1. Approved asset cache.
2. Stock video.
3. Stock image.
4. Document or screenshot.
5. Data visualization.
6. AI-generated image.
7. Typography fallback.

The pipeline must not silently use an inappropriate fallback. For example, Fal.ai Flux should be treated according to its actual supported role as an AI-image fallback, not assumed to generate arbitrary cinematic video or documentary material. 

## 7.3 Asset quality tests

Check:

- Resolution.
- Aspect ratio.
- Duration.
- Download accessibility.
- File integrity.
- Correct media type.
- Crop and focal point.
- Visual relevance.
- Duplicate usage.
- Broken URLs.
- Missing assets.
- Portrait and low-resolution assets.

## 7.4 Provenance and licensing tests

Every production asset should record:

- Provider.
- Source URL.
- Stored URL.
- Creator, where applicable.
- License.
- Acquisition date.
- Allowed usage.
- Dimensions.
- Duration.
- Checksum.
- Generated-asset metadata.
- Selection reason.

A missing license or provenance record should be a quality blocker for production assets.

---

# 8. Validate the Remotion renderer

The renderer must be deterministic and receive an executable manifest, not unresolved creative instructions.

## 8.1 Manifest validation

Before rendering, confirm:

- Every frame is covered.
- Shots do not overlap unintentionally.
- Required assets exist.
- All component names are supported.
- Component props satisfy the schema.
- Every statistic has a claim reference.
- All captions have valid timing.
- Audio and music cues are complete.
- The manifest references consistent artifact revisions.

These are explicit acceptance requirements for the renderer-manifest stage. 

## 8.2 Component contract tests

For every Remotion component, test:

- Valid props.
- Missing props.
- Invalid enum values.
- Empty text.
- Long text.
- Large numbers.
- Currency values.
- Non-ASCII text.
- Missing assets.
- Portrait assets.
- Low-resolution images.
- Empty chart series.
- Unsupported combinations.
- Safe-area behavior.
- Fallback rendering.

The initial component set should be tested at minimum for:

- `CinematicMedia`
- `FullScreenTypography`
- `BigNumber`
- `StatCard`
- `Chart`
- `Timeline`
- `QuoteCard`
- `DocumentCard`

The renderer plan specifically calls for a visual gallery and edge-case tests for these kinds of inputs. 

## 8.3 Determinism test

Render the same manifest multiple times.

Compare:

- Frame count.
- Duration.
- Audio placement.
- Shot boundaries.
- Selected reference frames.
- Hashes or perceptual similarity of rendered frames.
- Final output dimensions and codec properties.

The expected result is identical or acceptably equivalent output for the same manifest, configuration, assets, and component versions.

## 8.4 Visual regression test

Create a renderer gallery containing:

- Normal examples.
- Maximum-length text.
- Missing data.
- Fallback assets.
- Bright and dark backgrounds.
- Portrait and landscape media.
- Charts with large and small values.
- Long captions.
- Impact typography.
- Document highlights.
- Timeline transitions.

Store approved reference frames and compare future renders against them using:

- Pixel difference for deterministic regions.
- Perceptual similarity for animated or anti-aliased regions.
- Manual review for intentional changes.

## 8.5 Audio/video synchronization tests

Verify:

- Audio duration equals the manifest duration.
- Narration starts at the expected frame.
- Captions appear at the correct word timestamps.
- Impact typography appears on the intended words.
- Music ducks under narration.
- SFX are not clipped.
- No unintended silence occurs.
- No audio overlaps violate the audio plan.
- Final muxing preserves the expected sample rate and channels.

---

# 9. Validate quality gates and human approvals

Quality evaluation must use hard blockers, warnings, model-assisted diagnostics, and preview inspection rather than one opaque score. 

## 9.1 Hard blocker tests

The quality gate must block the project for:

- Invalid artifact schema.
- Unsupported critical claim.
- Missing narration.
- Missing required asset.
- Missing or invalid license metadata.
- Invalid shot timing.
- Missing payoff where required.
- Failed render.
- Caption overflow.
- Unresolved renderer component.
- Inaccessible required media.
- Missing approval when approval is required.

## 9.2 Warning tests

Warnings may include:

- Weak hook.
- Repetitive visuals.
- Long exposition.
- Excessive caption density.
- Excessive SFX density.
- Low-confidence asset relevance.
- Long visually static intervals.

Warnings should identify:

- Severity.
- Confidence.
- Evidence.
- Artifact ID.
- Beat or shot ID.
- Suggested correction.

## 9.3 Preview-render audit

Render a low-resolution preview and inspect:

- Black frames.
- Empty frames.
- Frozen media.
- Incorrect crops.
- Caption overflow.
- Repeated visuals.
- Abrupt audio transitions.
- Unintended silence.
- Poor contrast.
- Incorrect typography.
- Missing assets.
- Misaligned shot boundaries.

The quality plan specifically requires these checks to operate on actual preview output, not only JSON artifacts. 

## 9.4 Approval workflow tests

Confirm that the workflow supports:

- Script approval.
- Script revision request.
- Preview approval.
- Selected-section regeneration.
- Title approval.
- Thumbnail approval.
- Publication approval.
- Rejection.
- Approver identity.
- Timestamp.
- Artifact revision.
- Approval notes.
- Approval invalidation when an approved artifact changes.

The existing Telegram approval is only an intake/topic gate; it is not currently a publication gate. The expanded system must explicitly add preview and publication approval states. 

---

# 10. Validate targeted regeneration

Test that the system can regenerate only the affected artifact:

- A single story beat.
- A single shot.
- A single asset.
- A caption plan.
- A music cue.
- A thumbnail.
- A script section.

Verify that:

- Unaffected artifacts retain their IDs and revisions.
- Changed artifacts receive new revisions.
- Dependent artifacts are invalidated or regenerated.
- Approved facts remain unchanged.
- The final manifest uses the correct mixed artifact graph.
- Before-and-after diffs are stored.
- Retry limits are enforced.
- Human review is triggered after the configured limit.

A regeneration should not silently rebuild the entire project unless explicitly requested.

---

# 11. Validate security and operational safeguards

Test:

- Secrets are not committed or printed in logs.
- API keys are redacted.
- OAuth tokens are protected.
- Unpublished assets are private or signed where appropriate.
- Supabase RLS policies protect project data.
- Public URLs are not exposed prematurely.
- Per-video cost ceilings are enforced.
- Per-stage cost ceilings are enforced.
- Regeneration budgets are enforced.
- Logs contain correlation IDs but no credentials.
- Failed jobs do not leave orphaned public assets.
- Temporary local files are cleaned up.
- Renderer paths are configurable rather than machine-specific.

This is important because the baseline identifies public storage assumptions, hard-coded local paths, and local OAuth files as operational risks. 

---

# 12. Validate analytics instrumentation separately

Analytics should first confirm what was produced, not immediately attempt to optimize generation.

At publication time, freeze an `AnalyticsFeatureVector` containing:

- Topic category.
- Hook type and duration.
- Story-beat distribution.
- Open-loop count.
- First-minute shot rate.
- Overall shot-rate distribution.
- Component distribution.
- Pattern-interrupt count.
- Caption-style distribution.
- Music profile.
- SFX density.
- Title strategy.
- Thumbnail strategy.
- Style-profile version.
- Model, prompt, schema, and configuration versions.
- Human overrides.

The analytics design explicitly requires this vector to be frozen at publication and recommends delaying automatic optimization until enough evidence exists. 

Test that:

- Every published video has exactly one frozen feature vector.
- Human overrides are stored separately.
- The vector references the actual published artifact revisions.
- Analytics ingestion is idempotent.
- Historical snapshots are not overwritten.
- Retention intervals can be mapped back to beats and shots where data permits.
- Conclusions include sample size and uncertainty.
- No automated generation rule is created from an unvalidated correlation.

---

# 13. End-to-end test scenarios

Create a reusable scenario suite.

## Scenario A: Successful production

1. Submit a topic through Telegram.
2. Approve the topic.
3. Run the new pipeline.
4. Generate all artifacts.
5. Resolve assets.
6. Produce preview.
7. Approve preview.
8. Render final output.
9. Approve publication.
10. Upload to YouTube.
11. Verify analytics feature vector.

Expected result: all stages complete, all artifacts are linked, approvals are recorded, and the published package matches the approved preview and metadata.

## Scenario B: Invalid model output

Return malformed script JSON or an invalid enum.

Expected result:

- Schema validation fails.
- No downstream stage runs.
- The run is classified as invalid model output.
- The error is visible to the operator.
- No partial publication occurs.

## Scenario C: Timestamp mismatch

Return incomplete or inconsistent ElevenLabs timestamps.

Expected result:

- Mismatch is detected.
- Fallback alignment is attempted where safe.
- Critical failures block the pipeline.
- No incorrectly synchronized render is produced.

## Scenario D: Asset provider failure

Make Pexels unavailable and Fal.ai unavailable.

Expected result:

- Fallback hierarchy is followed.
- The selected fallback is recorded.
- The project blocks only if no acceptable fallback remains.

## Scenario E: Renderer failure

Terminate Remotion during rendering.

Expected result:

- Render stage is marked failed.
- No publication occurs.
- Existing artifacts remain valid.
- Resume does not repeat completed billable stages.

## Scenario F: Concurrent orchestrators

Run two local orchestrators against one approved project.

Expected result: one process owns the lease; the other does not duplicate work.

## Scenario G: Post-approval modification

Approve the preview, then modify the shot plan or thumbnail.

Expected result:

- The previous approval is invalidated.
- A new approval is required.
- Publication cannot proceed with stale approval.

## Scenario H: Publish retry

Make the YouTube upload fail after the video has been uploaded but before local state is updated.

Expected result:

- The system detects or records the external upload ID.
- A retry does not create an unintended duplicate upload.
- Final publication state is reconciled safely.

---

# 14. Define the acceptance gates

The expansion should be accepted only if all of the following are true.

## Gate 1: Contract integrity

- All artifacts validate.
- Python and TypeScript schemas agree.
- Artifact revisions and parent references are correct.
- Legacy migration works.

## Gate 2: Pipeline integrity

- All stages run in the intended order.
- Invalid inputs stop before external calls.
- Outputs are persisted before state advances.
- Resume, retry, and restart behavior work.

## Gate 3: Timing integrity

- Every narration word maps to a beat.
- Every shot has valid boundaries.
- No unintended gaps or overlaps exist.
- Captions and events align with word timestamps.
- Duration matches the audio.

## Gate 4: Renderer integrity

- Every manifest component is supported.
- Missing or invalid props fail before rendering.
- Fallbacks work.
- No black frames, frozen assets, overflow, or missing audio occur.
- Repeated renders are deterministic.

## Gate 5: Editorial integrity

- The script fulfills the promise.
- Factual claims are source-grounded.
- Statistics and documents have claim references.
- The payoff is present.
- Visual choices have narrative purpose.
- The result does not rely solely on an uncalibrated quality score.

## Gate 6: Operational integrity

- Concurrent processing is prevented.
- External failures are classified.
- Retry limits and cost ceilings work.
- Secrets and unpublished assets are protected.
- Logs are sufficient for diagnosis.

## Gate 7: Approval and publication integrity

- Script and preview approvals are recorded.
- Publication approval is required when enabled.
- Stale approvals cannot authorize changed artifacts.
- The published package exactly matches the approved package.
- Failed or unapproved projects cannot reach YouTube.

## Gate 8: Analytics integrity

- A feature vector is frozen for each published video.
- Human overrides are preserved.
- Metrics are ingested idempotently.
- Findings include uncertainty and sample size.
- No unsupported automated optimization occurs.

---

# 15. Recommended execution order

Use this order to avoid testing downstream behavior before the foundation is reliable:

1. **Code and repository inventory**
2. **Baseline and golden-fixture capture**
3. **Database and artifact schema validation**
4. **Stage runner, locking, idempotency, and resume tests**
5. **Editorial and claim-provenance tests**
6. **Timing compiler and shot-plan tests**
7. **Asset and rights tests**
8. **Remotion component and manifest tests**
9. **Preview and quality-gate tests**
10. **Human approval workflow tests**
11. **Final rendering and publishing tests**
12. **Analytics instrumentation tests**
13. **Shadow-mode comparison against the legacy pipeline**
14. **Pilot production run**
15. **Production rollout with rollback enabled**

The recommended implementation order in the architecture similarly places contracts and artifact versioning first, followed by story/retention systems, timing and scene direction, renderer components, quality approval, publishing, and analytics. 

# Final evaluation outcome

At the end of this process, produce a verification report with one of three decisions for every implementation series:

- **PASS** — implemented and verified against automated and behavioral tests.
- **PASS WITH WARNINGS** — functionally works, but has non-blocking issues or unverified edge cases.
- **FAIL** — missing, incorrectly integrated, unsafe, nondeterministic, or inconsistent with the target contract.

The most important principle is:

> Do not evaluate the expansion only by checking whether new files exist or whether one video rendered successfully. Evaluate whether the complete artifact graph, state machine, timing model, renderer manifest, quality system, approvals, and publication result are correct, repeatable, recoverable, and traceable.

The supplied architecture documents themselves caution that documentation is not enough to verify prompt behavior, timestamp alignment, renderer sophistication, test coverage, asset rights, security, or failure recovery; those areas must be established through source inspection and executable tests.
