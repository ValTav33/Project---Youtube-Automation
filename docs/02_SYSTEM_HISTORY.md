# System History (V1 to V2)

This document provides context on how the Youtube Automation Pipeline evolved from its initial V1 architecture to the current V2 architecture, ensuring future developers understand the reasoning behind the current decoupled setup.

## The V1 Architecture (Legacy)
The original pipeline was designed to be fully cloud-based and heavily relied on basic Python scripts.

- **Stack:** Python, MoviePy, OpenAI.
- **Workflow:** Everything ran on a single Python backend (often hosted on Railway). A cron job or Telegram webhook triggered the pipeline. The system would generate a script using a single API call, generate TTS, and then use `MoviePy` to stitch static images together.
- **The Problem:** 
  1. **Rendering Limits:** Cloud providers (like Railway or Heroku) have strict memory, CPU, and disk limits. Video rendering via `MoviePy` frequently ran out of memory (OOM) or took hours for a simple short. 
  2. **Visual Quality:** `MoviePy` is extremely rudimentary. Creating complex animations, text pop-ins, kinetic typography, or dynamic transitions is prohibitively difficult in Python.
  3. **Script Quality:** Relying on a single prompt to generate an entire video resulted in generic, unengaging content.

## The V2 Architecture (Current)
To solve the V1 limitations, the architecture was fundamentally split and upgraded on two fronts:

### 1. Shift to Local Rendering with Remotion
To achieve professional-grade animations and visual fidelity, the rendering engine was switched from Python `MoviePy` to **Remotion** (React). Because Remotion uses headless Chrome and FFmpeg, it is extremely resource-intensive. Therefore, the rendering phase was **moved off the cloud** and delegated entirely to a dedicated Local Mac (`orchestrator.py`), bypassing cloud infrastructure limits entirely.

### 2. Multi-Agent Scripting
To combat generic AI scripts, a deeply multi-agent workflow was built. Instead of one large prompt, V2 uses isolated specialized agents (Research, Angle, Marketing, Scripting, Critic, Scene Director). They communicate by saving and reading **Artifacts** in Supabase, acting like a virtual production studio. 

### 3. State Management via Supabase
Because the system is now split (Telegram UI on Cloud vs. Rendering on Local Mac), **Supabase** acts as the central brain. The Cloud bot updates the database state, and the Local Mac continuously polls the database to see if it should begin rendering or generation.

**Summary:** The V2 architecture trades cloud simplicity for local power, utilizing the cloud only for the Telegram human-in-the-loop control while maximizing the visual output via Local React rendering and multi-agent logic.
