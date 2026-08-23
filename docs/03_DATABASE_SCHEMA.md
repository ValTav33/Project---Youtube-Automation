# Supabase Database Schema

Because the V2 architecture separates Cloud (Telegram bot) and Local (Orchestrator and Render), Supabase is the single source of truth for both state and content.

## 1. Table: `videos`
This is the core table representing the lifecycle of a video project.

### Core Columns:
- `id` (UUID): Primary key.
- `target_title` (String): The initial rough title injected by the user or discovery agent.
- `topic_premise` (String): The initial context or prompt outlining what the video should be about.
- `status` (Enum `video_status`): The most critical field, driving the state machine.

### `video_status` Enum Values:
- `discovered`: Newly found topic.
- `approved`: Ready for the AI pipeline to begin generation. The local Orchestrator polls for this.
- `scripting`: The AI is currently generating the scripts, scenes, and artifacts.
- `voiceover` / `visuals`: (Legacy or optional steps).
- `awaiting_publish_approval`: The AI pipeline finished and sent a Telegram message. Waiting for human click.
- `rendering`: The user clicked Approve, and the Local Mac is currently running Remotion.
- `publishing`: Render is done, currently uploading to YouTube.
- `published`: Upload complete.
- `failed`: An error occurred.

## 2. Table: `artifacts`
Instead of storing massive JSON payloads directly on the `videos` table, the V2 pipeline uses the `artifacts` table. Each AI Agent in the pipeline saves its output as a unique row in this table.

### Core Columns:
- `id` (UUID): Primary key.
- `video_id` (UUID): Foreign key linking back to the `videos` table.
- `artifact_type` (String): Identifies the agent that created it (e.g., `StoryScript`, `ResearchPacket`, `RendererManifest`).
- `content` (JSONB): The actual structured JSON output produced by the agent.
- `revision` (Integer): Allows for version control of artifacts in case of regenerations.

## 3. Table: `global_performance`
Tracks the aggregate scoring and feedback applied across all videos. The `LearningEngine` agent reads this table at the very beginning of the pipeline to apply past learnings (e.g., "Keep pacing faster") to the new video's prompt.

### Core Columns:
- `id` (UUID): Primary key.
- `feedback_type` (String): e.g., "Pacing", "Visuals", "Script".
- `guidance` (String): The instruction for the AI (e.g., "Always ensure intro is under 5 seconds").
