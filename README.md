# Automated YouTube Production Engine

An API-driven orchestrator, cloud database, and programmatic rendering pipeline for generating 8-to-10 minute data-rich YouTube video essays.

## 🚀 Overview

This project automates the creation of high-retention, fast-paced YouTube documentary/case study videos. The system leverages a **hybrid deployment architecture**:
- **Telegram Bot (`telegram_bot.py`)**: Runs 24/7 on **Railway** to receive topic ideas, display the queue, and handle human-in-the-loop approvals anytime, anywhere.
- **Pipeline Orchestrator (`orchestrator.py`)**: Runs **Locally (Mac)** to handle the heavy lifting (video rendering) when the machine is awake.
- **Supabase** (PostgreSQL) for state management and database tracking.
- **OpenAI GPT-4o** for structured JSON script generation.
- **ElevenLabs API** for highly realistic voiceovers with word-level timestamps.
- **Remotion** for programmatic video composition (dynamic subtitles, Ken Burns effects, stat callouts).
- **Fal.ai & Pexels** for visual asset sourcing (stock & AI-generated b-roll).
- **YouTube API** (via Python) for automated uploading and publishing.

## 🏗️ Architecture

The pipeline consists of the following steps:
1. **Topic Discovery & Intake**: You can send any topic idea directly to your Telegram Bot (running on Railway), which saves it as a draft in Supabase.
2. **Approval Gate**: You review the queue and tap "Approve" inside Telegram. The bot updates the database status to `approved`.
3. **Pipeline Daemon (Local)**: The `src/orchestrator.py` daemon runs locally, polls Supabase for approved videos, and drives the rest of the workflow.
4. **Script Generation**: GPT-4o crafts a highly structured 35-45 scene JSON script based on the approved topic.
5. **Voiceover & Timestamps**: The script is sent to ElevenLabs to generate the audio track and precise word-level timestamps.
6. **Visual Sourcing**: Pexels is queried for stock B-roll; Fal.ai (Flux) serves as a fallback for custom AI generation.
7. **Rendering**: A local headless Remotion instance assembles the audio, visual assets, subtitles, and effects into a polished MP4.
8. **Publishing**: The final video and AI-generated thumbnail are automatically uploaded to YouTube via the Python Google API Client.

## 📂 Project Structure

- `/src`: Core Python scripts handling various steps of the pipeline (e.g., `orchestrator.py`, `script_generator.py`, `audio_generator.py`, `publisher.py`, `asset_resolver.py`).
- `/scripts`: Miscellaneous utility scripts, including `telegram_bot.py`.
- `/remotion`: React-based Remotion video composition and layouts.
- `/renderer-service`: The Next.js / Remotion server for rendering videos locally.
