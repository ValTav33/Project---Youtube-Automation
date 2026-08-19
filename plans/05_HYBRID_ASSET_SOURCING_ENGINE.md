# Plan 05: Hybrid Visual Sourcing Engine

## Status: ✅ COMPLETED & TESTED

### 1. Goal
Asynchronously gather 1080p stock video clips or AI-generated cinematic images for each of the 35–45 scenes in the script payload.

---

### 2. Implementation File
- **Asset Resolver:** [src/asset_resolver.py](file:///Users/valsamis/Documents/Project%20-%20Youtube%20Automation/src/asset_resolver.py)

---

### 3. Resolution Priority

1. **Pexels Video API (Stock B-Roll):**
   - Query: `scene.broll_search_query`
   - Orientation: `landscape` (1920x1080)
   - Asset Type: `video`

2. **Fal.ai Flux Schnell (Generative Fallback):**
   - Prompt: `"Cinematic 4K documentary b-roll, hyper-realistic, dramatic lighting, high contrast: {query}"`
   - Size: `landscape_16_9`
   - Steps: `4`
   - Asset Type: `image`

All resolved URLs (`asset_type` + `asset_url`) are linked back into the Supabase video record `script_payload.scenes`.
