# YouTube Automation Pipeline (V2 Architecture)

Welcome to the YouTube Automation Pipeline! This project is a fully automated, agentic AI system that generates, renders, and publishes YouTube Shorts autonomously, with a human-in-the-loop review step via Telegram.

## Quick Start

This pipeline is split into two primary environments:
1. **Cloud Environment (Railway):** Runs the Telegram Bot interface.
2. **Local Environment (Mac):** Runs the AI Orchestrator and the heavy rendering workloads.

### 1. Cloud (Railway)
The cloud service is strictly responsible for handling user interactions via Telegram.
- **Entrypoint:** `scripts/telegram_bot.py`
- **Environment Variables required:** `TELEGRAM_BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

### 2. Local (Mac)
The local machine does the heavy lifting: running AI agents, synthesizing voice, compiling React code via Remotion, and uploading to YouTube.
- **Entrypoint:** `python src/orchestrator.py poll` (Keep this running in the background)
- **Environment Variables required:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `TELEGRAM_BOT_TOKEN`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`.

## How to learn more

To fully understand the codebase, the history, and the architecture, please read the documentation in the `/docs` folder:
- **[01_ARCHITECTURE.md](./docs/01_ARCHITECTURE.md):** The core system design, multi-agent pipeline, and data flow.
- **[02_SYSTEM_HISTORY.md](./docs/02_SYSTEM_HISTORY.md):** The evolution from V1 (Python/MoviePy) to V2 (Agentic/Remotion).
- **[03_DATABASE_SCHEMA.md](./docs/03_DATABASE_SCHEMA.md):** Documentation of the Supabase enums, tables, and state machine.
- **[04_FILE_DIRECTORY.md](./docs/04_FILE_DIRECTORY.md):** A complete, file-by-file breakdown of what every script in the codebase does.

*Note: This system relies heavily on Supabase for state management between the isolated cloud and local environments.*
