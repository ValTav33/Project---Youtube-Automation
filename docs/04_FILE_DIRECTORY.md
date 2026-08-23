# File Directory & Component Breakdown

This document provides a file-by-file explanation of the V2 architecture, mapping out what every critical script does. This is the definitive guide to understanding the codebase.

## 1. Orchestration & State
- **`src/orchestrator.py`**: The "heartbeat" of the local machine. It runs continuously as a daemon, polling the Supabase `videos` table every 10 seconds. When it finds a video with `status="approved"`, it triggers `run_v2.py`. When it finds one with `status="awaiting_publish_approval"`, it triggers local rendering (`render_v2.py`).
- **`scripts/telegram_bot.py`**: The Telegram UI layer intended to run 24/7 on a cloud provider (e.g., Railway). It listens for user inputs (like "Approve & Render") and updates the Supabase status accordingly, effectively passing control back to the local `orchestrator.py`.

## 2. Multi-Agent Pipeline Core
- **`src/run_v2.py`**: The main entry point for the Multi-Agent Generation phase. It strings together all the agents in a sequential pipeline.
- **`src/stage_runner.py`**: A crucial utility wrapper used by every agent. It checks Supabase to see if an `Artifact` for a specific stage already exists. If it does, it skips the execution (saving time and tokens). If it doesn't, it runs the agent and saves the JSON output back to Supabase.
- **`src/contracts.py`**: Contains Pydantic models. These define the exact JSON structure that every agent must strictly output (e.g., `StoryScript`, `RendererManifest`).

## 3. The AI Agents
- **`src/story_engines.py`**: Contains the majority of the LLM prompt logic. It houses:
  - `Research Agent`: Gathers factual context.
  - `Angle Selector`: Decides the narrative hook.
  - `Marketing Strategist`: Plans SEO and thumbnail concepts.
  - `Script Writer`: Generates the actual voiceover text.
  - `Retention Critic`: Evaluates the script for pacing issues.
  - `Script Rewriter`: Fixes the script based on the Critic's feedback.
- **`src/learning_engine.py`**: The very first agent that runs. It fetches `global_performance` feedback from Supabase (e.g., "Always make intros faster") so the rest of the agents can apply these learnings.
- **`src/quality_gate.py`**: Evaluates the final rewritten script out of 10. If the score is too low, the pipeline is halted, preventing bad videos from being rendered.
- **`src/scene_director.py`**: Takes the final script and breaks it down into visual scenes, planning the timing, captions, and overall `RendererManifest` that Remotion needs.

## 4. Media & Assets
- **`src/voice_compiler.py`**: Synthesizes the text script into audio files (using ElevenLabs or OpenAI TTS) and saves them locally.
- **`src/asset_planner.py` & `src/asset_resolver.py`**: Determines what visual assets (images, stock footage) are needed for each scene and resolves them to local file paths so Remotion can use them.
- **`src/publish_planner.py` & `src/publisher.py`**: Handles packaging the final metadata (Title, Description, Tags) and sending the "Approve & Render" message to Telegram along with a mock/generated thumbnail.

## 5. Rendering & Uploading
- **`src/render_v2.py`**: The bridge between Python and React. It takes the `RendererManifest` JSON, saves it where Remotion can read it, and spawns the `npx remotion render` shell command. It also parses Remotion's output to update progress.
- **`/remotion/` (Directory)**: A standalone React project. It contains the logic to draw captions, render images, and compile everything into a final 60fps MP4 video using headless Chrome.
- **`src/youtube_auth.py` & `src/youtube_uploader.py`**: Handles OAuth2 authentication with Google and the final API calls to upload the MP4 and custom thumbnail to YouTube.

## 6. Utilities & Scripts
- **`/scripts/` (Directory)**: Contains utility scripts for debugging and manual interventions.
  - `inject_test.py`: Injects a fake video row into Supabase to trigger the pipeline for testing.
  - `reset_status.py`: Manually changes a video's status (e.g., back to `approved`) to force the orchestrator to retry it.
