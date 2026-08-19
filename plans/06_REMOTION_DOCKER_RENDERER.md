# Plan 06: Remotion Programmatic Video Rendering Engine

## Status: ✅ COMPLETED & COMPILED

### 1. Goal
Programmatically assemble visual clips, kinetic subtitles, spring-animated data callouts, and audio into an exportable 1080p MP4 documentary video via headless Chromium on Railway.

---

### 2. Implementation Files
- **Remotion Composition:** [remotion/src/Composition.tsx](file:///Users/valsamis/Documents/Project%20-%20Youtube%20Automation/remotion/src/Composition.tsx)
- **Railway Server Entrypoint:** [renderer-service/src/server.ts](file:///Users/valsamis/Documents/Project%20-%20Youtube%20Automation/renderer-service/src/server.ts)
- **Railway Dockerfile:** [renderer-service/Dockerfile](file:///Users/valsamis/Documents/Project%20-%20Youtube%20Automation/renderer-service/Dockerfile)

---

### 3. Composition Features
- **Kinetic Subtitles:** Dynamic active word highlighting in yellow (`#FFE600`) with scale punch (`1.15x`).
- **Ken Burns Effect:** Smooth slow zoom across image and video assets (`scale: 1.0 -> 1.15`).
- **Data Metric Overlays:** Spring-animated pop-in cards for statistics (`headline` + `stat_callout`).
- **Audio Ducking:** Voiceover at 1.0 volume + background ambient music at 0.12 volume.

---

### 4. Railway Microservice API
- **Endpoint:** `POST /api/render`
- **Request Body:** `{ "videoId": "uuid", "inputProps": { "scenes": [...], "words": [...], "audioUrl": "..." } }`
- **Response:** `202 Accepted` (Processes rendering asynchronously, uploads MP4 to Supabase Storage `rendered-videos`, and updates database status to `rendered`).
