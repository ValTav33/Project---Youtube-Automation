#!/usr/bin/env python3
"""
GPT-4o Documentary Script Generation Engine
Generates 35-45 granular scene blueprints with visual directions, overlays, and sound design.
"""

import os
import sys
import json
import logging
from typing import List, Optional, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI
from supabase import create_client

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


# Pydantic Schemas for Strict Output Validation
class VisualOverlay(BaseModel):
    headline: Optional[str] = Field(default=None, description="Short bold punchy text (max 4 words)")
    stat_callout: Optional[str] = Field(default=None, description="e.g., $14.2 Billion or -42%")
    chart_type: Optional[Literal["none", "bar", "line", "donut"]] = Field(default="none")


class Scene(BaseModel):
    scene_id: int
    narration: str = Field(description="The exact spoken words for this scene (10-18 seconds of speech, ~25-45 words).")
    layout_type: Literal["STOCK_BROLL", "SPLIT_METRIC", "MAP_ANIMATION", "HEADLINE_CUTOUT"]
    broll_search_query: str = Field(description="3-5 specific stock video search terms (e.g. cargo container ship ocean storm)")
    visual_overlay: Optional[VisualOverlay] = None
    sfx: Optional[Literal["sub_bass_drop", "whoosh", "paper_rip", "typewriter", "camera_shutter", "none"]] = "none"


class ScriptMeta(BaseModel):
    title: str = Field(description="High CTR Click-Worthy Title")
    description: str = Field(description="Engaging description with timestamps and keywords")
    tags: List[str] = Field(description="List of relevant SEO tags")


class FullScriptPayload(BaseModel):
    meta: ScriptMeta
    scenes: List[Scene]


SYSTEM_PROMPT = """You are a master YouTube documentary scriptwriter specializing in high-retention, fast-paced video essays (similar to MagnatesMedia and ColdFusion).

MANDATORY OUTPUT REQUIREMENTS — DO NOT DEVIATE:
- You MUST produce EXACTLY 40 scenes (no more, no less).
- Each scene narration MUST be 30-45 words (approximately 12-18 seconds of speech).
- Total word count across ALL narrations MUST be between 1,200 and 1,500 words.
- Do NOT stop early. Do NOT summarize. Write ALL 40 scenes in full.

SCENE STRUCTURE RULES:
- Scenes 1-3: Explosive hook — start in media res with a shocking statistic, a dramatic moment, or an unfolding crisis. No introductions, no channel greetings.
- Scenes 4-10: Context & backstory — build the world of the story with vivid, specific details.
- Scenes 11-25: Core conflict/revelation — escalate tension, reveal surprising facts, use data and contrasts.
- Scenes 26-35: Turning point & analysis — show consequences, expert reactions, and deeper implications.
- Scenes 36-40: Resolution & powerful takeaway — end with a memorable, thought-provoking conclusion that earns a like and subscribe.

TONE: Dramatic, authoritative, analytical, fast-paced. Zero filler. Every sentence must earn its place.

OUTPUT FORMAT: Valid raw JSON only. No markdown fences. No commentary. Match the FullScriptPayload schema exactly."""


def generate_documentary_script(topic: str, context: Optional[str] = None, model: str = "gpt-4o") -> FullScriptPayload:
    """
    Generates a structured documentary script using OpenAI GPT-4o.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set in environment.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    user_prompt = (
        f"Produce a complete, gripping YouTube documentary script for the topic:\n\n"
        f"TOPIC: {topic}\n"
    )
    if context:
        user_prompt += f"\nBACKGROUND / OUTLIER PREMISE:\n{context}\n"
    user_prompt += (
        "\nCRITICAL REMINDER: You MUST write ALL 40 scenes. Each narration must be "
        "30-45 words. Do NOT cut short. The total narration word count MUST reach 1,200 words minimum. "
        "Every scene counts — write them all in full."
    )

    logger.info(f"Generating documentary script for: '{topic}' using {model}...")

    response = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format=FullScriptPayload,
        temperature=0.85,
        max_tokens=6000
    )

    parsed_script: FullScriptPayload = response.choices[0].message.parsed
    total_words = sum(len(s.narration.split()) for s in parsed_script.scenes)
    logger.info(f"Script generated successfully! Scenes: {len(parsed_script.scenes)} | Total Spoken Words: {total_words}")

    return parsed_script


def process_video_scripting(video_id: str):
    """
    Fetches video from Supabase, generates script, and updates database state.
    """
    if not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_SERVICE_ROLE_KEY is missing.")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    if not video:
        logger.error(f"Video {video_id} not found.")
        return

    sb.table("videos").update({"status": "scripting"}).eq("id", video_id).execute()

    try:
        script = generate_documentary_script(
            topic=video.get("target_title", ""),
            context=video.get("topic_premise", "")
        )

        sb.table("videos").update({
            "status": "scripted",
            "script_payload": script.model_dump(),
            "target_title": script.meta.title
        }).eq("id", video_id).execute()

        logger.info(f"✅ Video {video_id} successfully scripted and saved to Supabase.")
    except Exception as e:
        logger.error(f"Failed to generate script for video {video_id}: {e}")
        sb.table("videos").update({
            "status": "failed",
            "error_log": f"Script generation failed: {str(e)}"
        }).eq("id", video_id).execute()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        v_id = sys.argv[1]
        process_video_scripting(v_id)
    else:
        print("Usage: python src/script_generator.py <video_id_or_topic>")
