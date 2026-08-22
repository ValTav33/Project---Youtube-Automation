# Legacy Pipeline Baseline

This document captures the existing behavior of the legacy pipeline before evaluating the new target architecture. This serves as the reference point for evaluating idempotency, resumability, schema consistency, and renderer behavior.

## Existing Pipeline Stages (Legacy)
1. **Intake (`scripts/telegram_bot.py`)**: Accepts topic via Telegram bot, inserts into `videos` table.
2. **Orchestrator Polling (`src/orchestrator.py`)**: Local script polls Supabase for `approved` videos.
3. **Script Generation (`src/script_generator.py`)**: GPT-4o generates a JSON payload representing the script scenes.
4. **Voiceover & Timestamps (`src/audio_generator.py`)**: ElevenLabs API generates TTS audio (`.mp3`) and word-level timestamps.
5. **Visual Sourcing (`src/asset_resolver.py`)**: Iterates over scenes to fetch Pexels/Fal.ai visuals, resolving URLs inline within the script JSON.
6. **Local Rendering (`src/orchestrator.py` & `/renderer-service`)**: Passes the monolithic `script_payload` via `props.json` to Remotion. Local Remotion renders to an MP4.
7. **Publishing & Thumbnails (`src/publisher.py`)**: Pollinations generates thumbnail. Video is uploaded to YouTube via local OAuth credentials.

## Existing Status Transitions
- `discovered`
- `approved`
- `scripting`
- `voiceover`
- `visuals`
- `rendering`
- `publishing`
- `published`
- `failed`

## Existing Database Fields (`videos` Table)
State is highly concentrated in a single `videos` row:
- `id` (UUID)
- `source_type` (Enum)
- `source_video_id` (String)
- `target_title` (String)
- `topic_premise` (String)
- `status` (`video_status` Enum)
- `script_payload` (JSONB) - Contains script, resolved assets, AND render progress.
- `audio_url` (String)
- `transcript_timestamps` (JSONB)
- `rendered_video_url` (String)
- `thumbnail_urls` (Array of Strings)
- `youtube_video_id` (String)
- `error_log` (String)
- `created_at` / `updated_at` (Timestamps)

## Existing Supabase Storage Buckets
- `audio` (For ElevenLabs MP3s)
- `visuals` (For Pexels/Fal.ai assets)

## Existing External API Calls
- **OpenAI (GPT-4o)**: Generates the script.
- **ElevenLabs (eleven_turbo_v2_5)**: Generates audio and word-level timestamps.
- **Pexels API**: Fetches stock footage.
- **Fal.ai (Flux)**: Generates fallback AI images.
- **YouTube Data API v3**: Uploads the final video.
- **Pollinations**: Generates the thumbnail.

## Existing Remotion Props
The Remotion project receives a single, large `props.json` containing:
- The entire `script_payload` (with `resolved_url` injected inline).
- The `audio_url`.
- The `transcript_timestamps`.

## Existing Output Files
- `.mp4` rendered video (Hard-coded path: `/Users/valsamis/Movies/Automated/`).
- Local `props.json` temp files used during rendering.

## Existing Error Behavior
- Errors update the `status` to `failed` and write to the `error_log` field in the database.
- Lack of explicit resume behavior: if a stage fails, fixing the error and restarting often means repeating previously completed billable stages or manually patching the database state.

## Existing Rendering and Publishing Behavior
- **Rendering**: Happens locally via subprocess `npx remotion render`. It hard-codes 30 FPS. Render progress is patched continuously into the `script_payload` column in the database (causing concurrency risk).
- **Publishing**: Uses local `token.json` and `client_secrets.json` files for OAuth authentication to YouTube.

## Identified Legacy Constraints
- **Concurrency Risk**: Continual mutations on the `videos` row, especially `script_payload` for render progress.
- **Hard-coded Paths**: Local machine paths for MP4s (`/Users/valsamis/Movies/Automated/`) and local OAuth token files.
- **Hard-coded Settings**: Remotion is fixed at 30 FPS.
- **Idempotency/Resume**: No native state-machine resumability; restarting a video can cause duplicate billable API calls or duplicated work.
