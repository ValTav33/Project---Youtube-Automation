# Plan 03: GPT-4o Documentary Script Engine

## Status: ✅ COMPLETED & TESTED

### 1. Goal
Convert an approved topic or outlier concept into a high-retention 8–10 minute documentary script formatted as a structured JSON scene blueprint.

---

### 2. Implementation File
- **Script Generator:** [src/script_generator.py](file:///Users/valsamis/Documents/Project%20-%20Youtube%20Automation/src/script_generator.py)

---

### 3. Output Schema (Pydantic Enforced)
```json
{
  "meta": {
    "title": "High CTR Click-Worthy Title",
    "description": "Engaging description with timestamps and keywords",
    "tags": ["tag1", "tag2", "tag3"]
  },
  "scenes": [
    {
      "scene_id": 1,
      "narration": "The exact spoken words for this scene (25-45 words).",
      "layout_type": "STOCK_BROLL | SPLIT_METRIC | MAP_ANIMATION | HEADLINE_CUTOUT",
      "broll_search_query": "3-5 specific stock video search terms",
      "visual_overlay": {
        "headline": "Short bold punchy text (max 4 words)",
        "stat_callout": "e.g., $14.2 Billion or -42%",
        "chart_type": "none | bar | line | donut"
      },
      "sfx": "sub_bass_drop | whoosh | paper_rip | typewriter | camera_shutter | none"
    }
  ]
}
```

---

### 4. Pacing Rules
- **Total Duration:** 8–10 minutes (~1,200–1,400 words)
- **Scene Count:** 35 to 45 granular scenes
- **Scene Duration:** 10–18 seconds per scene
- **Hook:** First 3 scenes start immediately in media res with high stakes (no channel intros or fluff).
