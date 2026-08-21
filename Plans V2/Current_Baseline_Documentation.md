# Current Baseline Documentation

*This document captures the actual state, inputs, outputs, and behaviors of the pipeline prior to implementing the Phase 2 artifact-driven architecture.*

## 1. Module-by-Module Inputs and Outputs

### `src/orchestrator.py`
- **Purpose:** Coordinates the pipeline stages sequentially for a given `video_id`.
- **Inputs:** `video_id` from command line args.
- **Outputs:** Modifies the `status` field in Supabase iteratively (`scripting` -> `scripted` -> `audio_ready` -> `rendering` -> `rendered` -> `publishing` -> `published` or `failed`).
- **Dependencies:** Imports generation modules and `notifier.py`.
- **Behavior:**
  - Emits Telegram notifications at start, success, and failure of each major step.
  - Generates the Remotion `input_props` internally using `prepare_remotion_props()`.
  - Runs local Remotion rendering via a `subprocess.Popen` call to `npx remotion render`.
  - Parses standard output from the `npx remotion render` process to update `render_progress` inside the `script_payload` JSON.

### `src/script_generator.py`
- **Inputs:** `video_id` (used to fetch `target_title` and `topic_premise`).
- **Outputs:** Modifies `videos` record:
  - `status = 'scripted'`
  - `script_payload` (JSON payload matching `FullScriptPayload` Pydantic schema)
  - `target_title` (updated to GPT-generated title)
- **External Calls:** OpenAI GPT-4o (`chat.completions.parse`).

### `src/audio_generator.py`
- **Inputs:** `video_id` (fetches `script_payload.scenes` to extract narration).
- **Outputs:**
  - Uploads `video_id.mp3` to the `audio` Supabase Storage bucket.
  - Modifies `videos` record:
    - `status = 'audio_ready'`
    - `audio_url`
    - `transcript_timestamps` (JSON containing word-level timestamps and duration)
- **External Calls:** ElevenLabs API (`/v1/text-to-speech/.../with-timestamps`).

### `src/asset_resolver.py`
- **Inputs:** `video_id` (fetches `script_payload.scenes`).
- **Outputs:**
  - Modifies `videos` record:
    - Injects `asset_type` (image/video) and `asset_url` into the `script_payload.scenes` list.
- **External Calls:** Pexels API (Video), Fal.ai (Flux Schnell).

### `src/publisher.py`
- **Inputs:** `video_id`.
- **Outputs:**
  - Generates thumbnails via Pollinations Flux (no key needed).
  - Uploads thumbnails to the `thumbnails` Supabase Storage bucket.
  - Modifies `videos` record:
    - `thumbnail_urls`
    - `youtube_url` and `youtube_video_id`
    - `status = 'published'`
- **External Calls:** Pollinations Flux API, Google API Client (YouTube Data API v3).

### `src/notifier.py`
- **Inputs:** Video ID, Title, Event Status, Error Text.
- **Outputs:** HTTP POST to Telegram Bot API.
- **Behavior:** Fire-and-forget; handles its own errors silently so as not to crash the pipeline.

## 2. Supabase Data Model Access

Currently, all state is concentrated in a single row in the `videos` table:
- **Reads/Writes:** The orchestrator and worker scripts repeatedly read and write to the same `video` row, often pulling the entire record, mutating it, and updating it (`script_payload`, `transcript_timestamps`, `status`).
- **Concurrency Danger:** `render_progress` is continuously patched into the `script_payload` JSON field while the render runs, which could overwrite concurrent manual changes.
- **Storage Buckets Used:** `audio` and `thumbnails`.

## 3. Environment Variables Used

- `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID`
- `PEXELS_API_KEY`
- `FAL_KEY`
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`
- `REMOTION_RENDERER_URL` (Not currently used directly by `execute_local_remotion_render`, which calls `npx remotion render` directly instead of via an HTTP server).

## 4. Failure and Retry Behavior

- **Retries:** There are currently no explicit retry loops or backoff logic for external API failures (except for a basic HTTP timeout). If ElevenLabs or OpenAI fails, the Python script throws an Exception, sets `status = 'failed'`, and exits.
- **Idempotency:** A failed pipeline run must be restarted manually. State is not locked, though the orchestrator queue loop (`poll_approved_queue`) only pulls items where `status = 'approved'`. If a run fails midway (e.g., at rendering), its status is 'failed', meaning it won't be retried automatically.

## 5. Undocumented Assumptions and Hard-coded Paths

1. **Local Output Path:** `execute_local_remotion_render` hardcodes the output path to: `/Users/valsamis/Movies/Automated/{video_id}.mp4`
2. **Renderer Directory:** Assumes `os.path.join(os.getcwd(), "renderer-service")` exists and contains a valid Remotion project.
3. **Storage URLs:** Uses direct bucket paths instead of presigned URLs in most places.
4. **Frame Rate:** Hardcoded `FPS = 30` in `orchestrator.py`.
5. **OAuth Path:** `publish_to_youtube` looks for a local `token.json` file in the current working directory.
