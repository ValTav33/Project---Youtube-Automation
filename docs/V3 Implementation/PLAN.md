# V3 Roadmap — Professional Long-Form YouTube Production System

## Summary

Build V3 as a new, versioned pipeline beside the current system—do not try to patch every V2 artifact in place.

Target: English/global, 16:9, 8–12 minute business/tech mini-documentaries. The core principle is:

`story → visual argument → deterministic production manifest → Remotion → preview → targeted repair`

V3 will use one renderer, a bounded visual vocabulary, source-backed research, and explicit ownership for each agent. Existing V2 artifacts remain readable but new videos run with `pipeline_version = 3`.

## Roadmap

| Phase | Goal | Exit criterion |
|---|---|---|
| 0 | Secure and freeze the baseline | No exposed secrets; reproducible test run |
| 1 | Define one canonical workflow and contracts | V3 schema and state machine validated end-to-end with fixtures |
| 2 | Build the visual system before AI automation | Manually authored manifests render premium scenes reliably |
| 3 | Rebuild research and story production | A source-backed script is produced with strict role boundaries |
| 4 | Add visual, asset and audio production planning | A deterministic production manifest renders without creative guesswork |
| 5 | Add rough-cut QA, repair and human review | Preview feedback creates targeted revisions, not full reruns |
| 6 | Pilot, measure and introduce real learning | Ten reviewed videos and real analytics drive controlled iteration |

## Phase 0 — Security, baseline, and delivery safety

### Implementation plan

- Revoke and recreate the exposed Telegram credential; remove all hard-coded secrets and insecure defaults from source and repository history where possible.
- Move configuration to environment variables with a committed `.env.example` containing names only.
- Add a startup configuration validator: the orchestrator must fail before processing a job if any required secret, storage bucket, renderer path, or provider setting is missing.
- Add a minimal automated test command for Python contracts and a separate render/gallery command for Remotion.
- Capture one current V2 job and render output as a baseline artifact for comparison; it is diagnostic only, not a quality target.

### Done when

- Secret scanning passes locally and in CI.
- No production credential exists in tracked source.
- A fixture job can run without real publishing credentials.

## Phase 1 — Canonical workflow, contracts, and state ownership

### Implementation plan

- Make Pydantic contracts the source of truth; generate a versioned JSON Schema consumed by the TypeScript renderer. Remove divergent hand-maintained renderer schemas.
- Introduce these V3 artifacts:
  - `ChannelCreativeBible`: immutable channel identity, audience, visual rules, caption policy, source policy and prohibited clichés.
  - `VideoBrief`: topic, target duration, promise, audience tension, title/thumbnail hypothesis and creative-bible version.
  - `VerifiedResearchPacket`: claims tied to source URLs, publication dates, evidence notes and confidence.
  - `StoryBlueprint`: narrative beats, tension, claim references and intended payoff.
  - `VisualBriefPlan`: visual arguments and component choices per beat.
  - `ProductionManifest`: final deterministic timeline consumed by Remotion.
- Replace ambiguous statuses with one lifecycle:

  `discovered → approved → generating → awaiting_preview_approval → rendering → awaiting_publish_approval → publishing → published`

  Any failure transitions to `failed` with a recoverable stage/revision reference.
- Make the orchestrator the sole owner of state transitions; stages return artifacts only. Rendering and publishing each have one owner.
- Preserve historical V2 data without migration. V3 videos use new artifact types and schema versions.

### Done when

- Python validates every V3 artifact before persistence.
- Renderer validates the same manifest schema before rendering.
- A fixture can transition through every V3 state exactly once, including rejection and resume.

## Phase 2 — Remotion visual system and manual gallery

### Implementation plan

- Make `remotion/` the only production render package for local Mac rendering. Retire the duplicate `renderer-service` production path after parity is confirmed.
- Build a channel style pack: typography, color palette, grid, motion presets, transition vocabulary, visual safe areas and audio levels.
- Build eight high-quality, reusable 16:9 components:
  1. `CinematicMedia`
  2. `EvidenceCard`
  3. `BigNumber`
  4. `DataChart`
  5. `Timeline`
  6. `Comparison`
  7. `ProductScreen`
  8. `TypographyImpact`
- Each component supports valid long text, missing assets, dark/light media, crop control, source attribution where needed, and safe fallback behavior.
- Create a component gallery and manually authored manifests. Render representative sequences before connecting any agent.
- Define a small visual grammar mapping: claim type and narrative function determine allowed component types. For example, quantitative claims use `DataChart`, `BigNumber` or `Comparison`, never generic stock footage by default.

### Done when

- The gallery renders deterministically on the target Mac.
- Two manually authored 60–90 second sequences look on-brand and need no code changes after render.
- No component relies on an LLM decision at render time.

## Phase 3 — Source-backed research and story team

### Implementation plan

- Add a retrieval-backed Research stage through a provider adapter. Every factual claim must include source URL, publisher, date, evidence note and confidence.
- Add a Fact Verification stage that only validates or rejects claims; it does not choose the story angle or write narration.
- Refactor creative agents into strict ownership:
  - Strategy owns promise, target emotion, title and thumbnail hypothesis.
  - Story Architect owns beats, narrative tension and payoff order.
  - Script Writer owns spoken narration only.
  - Retention Editor owns revisions to narration only.
- Version every production prompt. Each prompt contains responsibility, non-responsibilities, input contract, output contract, editorial rules, forbidden behavior and acceptance criteria.
- Change the long-form script target from the current ~150-word Short format to an 8–12 minute narration budget, with beat-level length and source references.
- Block a script if it contains unsupported factual claims, unfulfilled title promise, missing payoff, or unsupported citation references.

### Done when

- One test topic produces a fact-checked, source-linked, long-form script.
- The script has no visual directions and every claim can be traced to approved research.
- Re-running a stage reuses the correct artifact revision without changing approved upstream decisions.

## Phase 4 — Visual, asset, audio, and manifest production

### Implementation plan

- Implement `VisualBriefPlan` as the bridge from narrative to editing. Each beat declares:
  - visual argument and evidence type;
  - preferred component and approved fallbacks;
  - visual role, emphasis/caption policy and motion intention;
  - source claim IDs when the visual represents a fact.
- Add a deterministic timeline compiler that maps actual voice timestamps to beats and shots. It must preserve camera motion, component directives and visual overlays.
- Build an Asset Curator stage that resolves assets against semantic requirements: subject, action, era, geography, focal point, visual role, crop and minimum quality.
- Stop using arbitrary generic fallbacks. Missing or unsuitable assets create a repair/review task; they do not silently become unrelated stock footage.
- Add provenance fields for every external asset: provider, licence category, source URL, resolution and suitability score.
- Add an Audio Plan with licensed music/SFX cues, narration ducking, transitions and emotional arc. Audio remains subordinate to picture quality in this phase.
- Compile one `ProductionManifest` containing only renderer-ready directives; Remotion must never infer what content to show.

### Done when

- Every rendered shot maps to a visual argument and a known component.
- Every asset can be traced, downloaded and rendered before the final render begins.
- The renderer receives no creative search queries, only resolved instructions and media.

## Phase 5 — Rough cut, visual QA, repair, and approval

### Implementation plan

- Add a low-resolution rough-cut render after the first manifest is compiled.
- Run deterministic technical QA: missing media, failed download, black frames, frozen clips, invalid crop, overlapping audio, caption overflow, timing gaps and duplicate assets.
- Generate a review package containing rough cut, thumbnail, title, script, source list and timestamped shot list.
- Add an `EditorRepairPlan` artifact. It may request an asset replacement, shot split, timing adjustment, component change or caption reduction; it cannot rewrite unrelated artifacts.
- Route repairs to the responsible owner only: asset issues to Asset Curator, visual issues to Visual Director, narration issues to Retention Editor.
- Keep the human approval gate after the actual preview and before public publishing.

### Done when

- A rejected preview produces a targeted new revision rather than a full pipeline restart.
- A valid preview can proceed to high-quality final render and publish approval.
- One artifact lineage records every repair and its cause.

## Phase 6 — Pilot programme and real analytics loop

### Implementation plan

- Produce ten V3 videos using the same channel bible and review process.
- Ingest actual YouTube metrics at defined intervals: impressions, CTR, average view duration, retention at 30 seconds/50%/90%, traffic source and subscriber conversion.
- Store the creative feature vector from the final manifest: hook type, promise category, beat structure, component distribution, visual density, title strategy and thumbnail strategy.
- Keep learning recommendations advisory until enough comparable videos exist; prohibit fabricated or simulated performance data.
- Review pilot outcomes manually and update the Creative Bible and prompt versions deliberately.
- Only after the long-form system is stable, create a separate Shorts adaptation pipeline with its own 9:16 components, durations and contracts.

### Done when

- Ten videos have complete creative, QA and analytics records.
- Prompt/style changes are tied to measured results, not guessed correlations.
- A documented V4 backlog exists based on actual production bottlenecks.

## Test plan

- Contract tests for every artifact, including Python-to-renderer schema compatibility.
- Unit tests for state transitions, artifact revisioning, timestamp-to-shot compilation and asset provenance rules.
- Visual regression tests for every Remotion component and representative full sequences.
- End-to-end fixture runs covering approval, rejection, targeted repair, resume, render failure and publishing failure.
- Manual acceptance review for each pilot video: source accuracy, visual relevance, pacing, audio mix, thumbnail/title promise and publish readiness.

## Assumptions

- One engineer executes phases sequentially; rough timing is 6–10 weeks before the ten-video pilot, excluding external API/account setup and review time.
- English/global business and technology stories remain the first channel niche.
- The user provides or approves licensed research, image, video and music providers before their related phase begins.
- Publishing stays private or unlisted until explicit human approval.
- No V2 historical artifact migration is required; V3 is introduced safely alongside it.
