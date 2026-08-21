# 01_Story_and_Retention_Engine.md

**Objective:**  
Build source-grounded scripts with strong hooks, open loops, escalation, reveals, and payoffs while avoiding unsupported claims and formulaic retention tactics.

**Dependencies:**

- `00_Pipeline_Contracts_and_Workflow_Foundation.md`
- Defined channel voice and editorial policy.
- Approved source-fetching or research workflow.

## Phase 1: Create the Promise Contract

*Define what the title, thumbnail, hook, and final story must deliver.*

- Implement `src/promise_engine.py`.
- Generate:
  - One-sentence viewer promise.
  - Central question.
  - Required payoff.
  - Working title candidates.
  - Thumbnail concepts.
  - Expected emotional arc.
  - Claims that must be proved.
  - Claims or wording that must not be used.
- Score title concepts for:
  - Clarity.
  - Specificity.
  - Curiosity.
  - Truthfulness.
  - Fit with the topic.
- Require the selected hook to address the same promise.
- Save all candidates and the selected version rather than discarding alternatives.

## Phase 2: Build the Research Packet

*Separate factual evidence from narrative writing.*

- Implement `src/research_engine.py`.
- Define approved source categories and trust levels.
- Collect source records with:
  - URL.
  - Publisher.
  - Author.
  - Publication date.
  - Retrieval date.
  - Relevant excerpt.
  - Source type.
- Extract atomic claims into a claim ledger.
- Mark claims as:
  - Verified.
  - Conflicting.
  - Uncertain.
  - Unsupported.
- Require numerical claims to include units, time periods, and source references.
- Prevent unsupported claims from entering charts, titles, thumbnails, or narration.
- Store direct quotations separately from paraphrases.

## Phase 3: Implement the Hook Engine

*Generate diverse opening strategies and choose one that can be fulfilled.*

- Implement `src/hook_engine.py`.
- Generate hook variants for:
  - Mystery.
  - Contradiction.
  - Narrative cold open.
  - High-impact statistic.
  - Consequence-first opening.
- Require each candidate to contain:
  - Hook text.
  - Hook type.
  - Estimated duration.
  - Open question.
  - Supporting claim references.
  - Expected payoff point.
- Score candidates using a separate evaluator context.
- Include these scoring dimensions:
  - Curiosity.
  - Immediate comprehension.
  - Novelty.
  - Emotional tension.
  - Factual support.
  - Title/thumbnail alignment.
  - Payoff feasibility.
- Initially retain human selection through Telegram.
- Record the selected hook type for later analytics.

## Phase 4: Implement the Story Engine

*Generate narrative beats rather than renderer-level shots.*

- Implement `src/story_engine.py`.
- Define a beat taxonomy:
  - `HOOK`
  - `SETUP`
  - `QUESTION`
  - `ESCALATION`
  - `REVEAL`
  - `CONTRADICTION`
  - `CONSEQUENCE`
  - `TWIST`
  - `CLIFFHANGER`
  - `PAYOFF`
  - `RESOLUTION`
- Give each beat:
  - Stable ID.
  - Purpose.
  - Narration.
  - Source references.
  - Open-loop IDs created or resolved.
  - Emotional tone.
  - Estimated duration.
  - Visual opportunity.
- Calculate target word count from the selected ElevenLabs voice’s measured speaking rate.
- Treat 35–45 as a target for story beats, not individual cuts.
- Require every open loop to have a planned payoff.
- Require the conclusion to resolve the Promise Contract instead of merely summarizing the topic.

## Phase 5: Implement the Retention Editor

*Review the story as an editor rather than regenerating it from scratch.*

- Implement `src/retention_editor.py`.
- Run separate passes for:
  - Hook strength.
  - Information density.
  - Repetition.
  - Predictability.
  - Transition quality.
  - Emotional variation.
  - Open-loop management.
  - Promise fulfillment.
- Estimate timeline positions from word count and voice profile.
- Flag long spans without:
  - New information.
  - A question.
  - A reveal.
  - A contradiction.
  - Escalation.
  - An emotional shift.
- Treat these as warnings unless they exceed the configured maximum.
- Rewrite only weak beats while preserving:
  - Beat IDs where possible.
  - Approved facts.
  - Source references.
  - Existing open-loop relationships.
- Limit automatic revision attempts.
- Produce a diff between the original and revised script.

## Phase 6: Add Script Validation and Evaluation

*Combine deterministic checks with subjective evaluation.*

- Validate:
  - Word count.
  - Required fields.
  - Unsupported claims.
  - Duplicate beats.
  - Unresolved open loops.
  - Hook duration.
  - Excessive exposition.
  - Missing payoff.
- Use model evaluation only for subjective dimensions.
- Save evidence for every quality finding, including beat IDs and excerpts.
- Reject scripts with unsupported critical claims.
- Send borderline scripts to Telegram for review instead of regenerating indefinitely.
- Build regression fixtures for several topic types:
  - Company rise and fall.
  - Technology history.
  - Financial scandal.
  - Product failure.
  - Founder profile.

**Acceptance Criteria:**

- Every factual beat references approved claims.
- Every open loop is resolved or explicitly marked as intentionally unresolved.
- Hook candidates are stored and scored.
- Weak sections can be revised without regenerating the complete script.
- Estimated narration length falls within the target range before TTS.
