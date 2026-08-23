#!/usr/bin/env python3
"""
ElevenLabs Audio & Word-Level Timestamp Generation Engine
Calls ElevenLabs API with timestamps, formats character alignment into word timestamps,
and uploads the generated MP3 to Supabase Storage.
"""

import os
import sys
import json
import base64
import logging
from typing import List, Dict, Any, Tuple
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam / standard deep doc voice
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def convert_alignment_to_word_timestamps(alignment: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float]:
    """
    Converts ElevenLabs character-level alignment into clean word-level timestamps.
    """
    characters = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])

    words = []
    current_word = ""
    start_time = None

    for idx, char in enumerate(characters):
        if start_time is None:
            start_time = starts[idx]

        if char == " " or idx == len(characters) - 1:
            if char != " ":
                current_word += char
            clean_word = current_word.strip()
            if clean_word:
                words.append({
                    "word": clean_word,
                    "start": round(start_time, 3),
                    "end": round(ends[idx], 3)
                })
            current_word = ""
            start_time = None
        else:
            current_word += char

    total_duration = words[-1]["end"] if words else 0.0
    return words, total_duration


def generate_speech_with_timestamps(
    full_text: str,
    voice_id: str = ELEVENLABS_VOICE_ID
) -> Tuple[bytes, List[Dict[str, Any]], float]:
    """
    Calls ElevenLabs TTS with timestamps and returns (audio_bytes, word_timestamps, total_duration).
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY is not set in environment.")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": full_text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    logger.info(f"Requesting voiceover from ElevenLabs for text ({len(full_text.split())} words)...")
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200:
        raise RuntimeError(f"ElevenLabs API error ({res.status_code}): {res.text}")

    data = res.json()
    audio_base64 = data.get("audio_base64", "")
    audio_bytes = base64.b64decode(audio_base64)
    alignment = data.get("alignment", {})

    words, duration = convert_alignment_to_word_timestamps(alignment)
    logger.info(f"Audio generated successfully! Total duration: {duration:.2f}s across {len(words)} words.")

    return audio_bytes, words, duration


def process_video_audio(video_id: str):
    """
    Pulls scripted scenes from Supabase, synthesizes narration audio,
    stores MP3 in Supabase Storage, and updates video timestamps.
    """
    if not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_SERVICE_ROLE_KEY is missing.")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    res = sb.table("videos").select("*").eq("id", video_id).single().execute()
    video = res.data

    if not video or not video.get("script_payload"):
        logger.error(f"Video {video_id} has no script_payload.")
        return

    scenes = video["script_payload"].get("scenes", [])
    full_narration = " ".join(s["narration"] for s in scenes)

    try:
        audio_bytes, words, duration = generate_speech_with_timestamps(full_narration)

        # Upload audio to Supabase Storage
        file_path = f"{video_id}.mp3"
        sb.storage.from_("audio").upload(
            path=file_path,
            file=audio_bytes,
            file_options={"content-type": "audio/mpeg", "upsert": "true"}
        )

        # Build public URL (SDK returns string directly in newer versions)
        public_url = sb.storage.from_("audio").get_public_url(file_path)
        audio_url = public_url if isinstance(public_url, str) else public_url.get("publicUrl", "")

        # Update Supabase video record
        sb.table("videos").update({
            "status": "audio_ready",
            "audio_url": audio_url,
            "transcript_timestamps": {
                "words": words,
                "total_duration_seconds": round(duration, 3)
            }
        }).eq("id", video_id).execute()

        logger.info(f"✅ Audio uploaded to: {audio_url}")
        logger.info(f"✅ Video {video_id} status → 'audio_ready' | Duration: {duration:.2f}s | Words: {len(words)}")

    except Exception as e:
        logger.error(f"Failed to generate audio for video {video_id}: {e}")
        sb.table("videos").update({
            "status": "failed",
            "error_log": f"Audio generation failed: {str(e)}"
        }).eq("id", video_id).execute()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        v_id = sys.argv[1]
        process_video_audio(v_id)
    else:
        print("Usage: python src/audio_generator.py <video_id>")
