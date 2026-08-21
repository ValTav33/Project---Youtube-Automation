# 07_YouTube_Analytics_and_Learning_Loop.md

**Objective:**  
Collect outcome data, connect it to creative decisions, support controlled experimentation, and eventually provide evidence-based recommendations to generation stages.

**Dependencies:**

- Published YouTube video IDs.
- Appropriate YouTube analytics authorization.
- Publication feature vectors.
- Sufficient video volume for meaningful comparisons.

## Phase 1: Instrument Creative Features at Publication

*Record what was produced before outcome data arrives.*

- Generate an `AnalyticsFeatureVector` containing:
  - Topic category.
  - Hook type.
  - Hook duration.
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
- Store model, prompt, schema, and configuration versions.
- Record human overrides separately from generated choices.
- Freeze this vector at publication.

## Phase 2: Implement Analytics Ingestion

*Collect available metrics using an idempotent scheduled process.*

- Add a scheduled cloud job rather than relying on the local Mac.
- Collect snapshots at configurable intervals such as:
  - Early.
  - Several days after publication.
  - One week.
  - Longer-term.
- Fetch available metrics for:
  - Impressions.
  - CTR.
  - Views.
  - Watch time.
  - Average view duration.
  - Average percentage viewed.
  - Likes.
  - Comments.
  - Subscribers gained.
  - Traffic source.
  - Retention data where account and API access permit it.
- Store raw snapshots before calculating derived metrics.
- Respect API quotas and retry requirements.
- Avoid overwriting historical snapshots.

## Phase 3: Build Retention and Outcome Analysis

*Turn raw data into comparable observations.*

- Interpolate retention at meaningful checkpoints when curve data is available.
- Calculate:
  - Initial drop.
  - First-minute retention.
  - Largest decline intervals.
  - Stable or replayed intervals.
- Map timeline intervals back to:
  - Story beats.
  - Shots.
  - Components.
  - Music sections.
  - Caption styles.
- Normalize comparisons by:
  - Video age.
  - Topic category.
  - Traffic-source mix.
  - Video duration.
  - Impression volume.
- Avoid ranking tiny samples as winners.

## Phase 4: Add Dashboards and Reports

*Make the feedback understandable before automating it.*

- Build channel-level reports for:
  - Hook performance.
  - Title and thumbnail strategy.
  - First-minute pacing.
  - Component usage.
  - Topic category.
  - Audio profile.
- Show uncertainty and sample size next to every conclusion.
- Provide drill-down from retention interval to script beat and preview frames.
- Mark observations as:
  - Descriptive.
  - Experimental.
  - Statistically reliable.
  - Insufficient data.

## Phase 5: Introduce Controlled Experiments

*Prefer causal tests over broad correlations.*

- Define experiment hypotheses before publication.
- Change one major variable at a time where possible.
- Record variant exposure periods.
- Establish minimum data requirements.
- Avoid comparing videos with fundamentally different audience sources as if they were equivalent.
- Keep a human decision-maker responsible for stopping or adopting tests.

## Phase 6: Feed Evidence Back into Generation

*Use validated lessons as bounded recommendations rather than unrestricted self-modification.*

- Create a `channel_learnings` artifact containing only supported findings.
- Include:
  - Finding.
  - Sample size.
  - Confidence.
  - Applicable topic categories.
  - Date range.
  - Expiration or review date.
- Retrieve only relevant learnings during hook, story, scene, and packaging generation.
- Keep general editorial rules separate from experimental channel findings.
- Require approval before a learning becomes a default generation rule.
- Log which learnings influenced each generated project.
- Roll back rules that stop performing.

**Acceptance Criteria:**

- Every published project has a frozen creative feature vector.
- Analytics ingestion is scheduled, idempotent, and quota-aware.
- Retention intervals can be mapped back to beats and shots when data permits.
- Findings display sample size and uncertainty.
- No automatic generation rule is adopted solely from an unvalidated correlation.
