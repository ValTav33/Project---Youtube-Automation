#!/usr/bin/env python3
"""
Telegram Approval Bot (Long-Poll Mode)
Polls Telegram every 2s for new messages/callbacks.
Saves topics to Supabase, sends approve/reject buttons.
Handles callbacks to update video status.

Run with: python3 scripts/telegram_bot.py
"""

import os
import sys
import time
import logging
import requests
import threading
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


# ── Telegram helpers ─────────────────────────────────────────────────────────

def send_message(chat_id: str, text: str, reply_markup: dict = None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    return r.json()


def answer_callback(callback_query_id: str, text: str = ""):
    requests.post(f"{BASE_URL}/answerCallbackQuery",
                  json={"callback_query_id": callback_query_id, "text": text},
                  timeout=5)


def approval_keyboard(video_id: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve:{video_id}"},
            {"text": "❌ Reject",  "callback_data": f"reject:{video_id}"}
        ]]
    }


# ── Supabase helpers ──────────────────────────────────────────────────────────

def insert_video(topic: str) -> Optional[dict]:
    if not supabase:
        logger.warning("Supabase not configured.")
        return None
    res = supabase.table("videos").insert({
        "source_type": "manual_telegram",
        "target_title": topic[:120],
        "topic_premise": topic,
        "status": "discovered"
    }).execute()
    return res.data[0] if res.data else None


def update_video_status(video_id: str, status: str, error_log: str = None):
    if not supabase:
        return
    payload = {"status": status}
    if error_log:
        payload["error_log"] = error_log
    supabase.table("videos").update(payload).eq("id", video_id).execute()


# ── Message handlers ─────────────────────────────────────────────────────────

def handle_message(msg: dict):
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "").strip()

    if not text:
        return

    if text.startswith("/start") or text.startswith("/help"):
        send_message(chat_id,
            "🎬 *YouTube Automation Engine*\n\n"
            "Send me any topic idea and I'll queue it for production review.\n\n"
            "Commands:\n"
            "/queue — View recent queue\n"
            "/help — This message"
        )
        return

    if text.startswith("/queue"):
        if not supabase:
            send_message(chat_id, "❌ Supabase not configured.")
            return
        rows = supabase.table("videos").select("id,target_title,status").order("created_at", desc=True).limit(8).execute().data or []
        if not rows:
            send_message(chat_id, "📋 Queue is empty.")
            return
        lines = [f"📋 *Recent Queue ({len(rows)} items)*\n"]
        status_emoji = {"discovered": "🔍", "approved": "✅", "scripting": "✍️",
                        "voiceover": "🎙️", "rendering": "🎬", "publishing": "⏳",
                        "published": "🚀", "failed": "❌"}
        for r in rows:
            emoji = status_emoji.get(r["status"], "⚪")
            lines.append(f"{emoji} `{r['status']}` — {r['target_title'][:50]}")
        send_message(chat_id, "\n".join(lines))
        return

    if text.startswith("/status"):
        if not supabase:
            send_message(chat_id, "❌ Supabase not configured.")
            return
            
        res = supabase.table("videos").select("id,target_title,status,script_payload").not_.in_("status", ["discovered", "failed", "published"]).order("updated_at", desc=True).limit(1).execute()
        rows = res.data or []
        
        if not rows:
            send_message(chat_id, "📭 No active videos currently in production.")
            return
            
        vid = rows[0]
        status = vid.get("status", "unknown")
        title = vid.get("target_title", "Untitled")[:50]
        payload = vid.get("script_payload") or {}
        
        status_map = {
            "approved": "⏳ Waiting in Queue (1/6)",
            "scripting": "✍️ Script Generation (2/6)",
            "voiceover": "🎙️ Audio Synthesis (3/6)",
            "visuals": "🖼️ Visual Assets (4/6)",
            "rendering": "🎬 Video Rendering (5/6)",
            "publishing": "📤 YouTube Upload (6/6)"
        }
        
        stage_text = status_map.get(status, f"🔵 {status}")
        
        msg = f"📊 *Live Status (from Mac)*\n\n🎬 *Video:* {title}\n🔄 *Stage:* {stage_text}"
        
        if status == "rendering":
            pct = payload.get("render_progress", 0)
            msg += f"\n⏳ *Progress:* {pct}% (Συνεχίζεται...)"
            
        send_message(chat_id, msg)
        return

    # Regular text → queue as new video topic
    logger.info(f"New topic intake: '{text}'")
    video = insert_video(text)

    if video:
        send_message(
            chat_id,
            f"💡 *Topic received!*\n\n`{text}`\n\n🆔 ID: `{video['id']}`\n\nApprove for production?",
            reply_markup=approval_keyboard(video["id"])
        )
    else:
        send_message(chat_id, "❌ Failed to save topic. Check Supabase connection.")


def handle_callback(callback: dict):
    query_id = callback["id"]
    chat_id = str(callback["message"]["chat"]["id"])
    data = callback.get("data", "")

    if ":" not in data:
        answer_callback(query_id, "Unknown action.")
        return

    action, video_id = data.split(":", 1)
    answer_callback(query_id, "Processing...")

    if action == "approve":
        update_video_status(video_id, "approved")
        send_message(chat_id,
            f"✅ *Approved!* Added to production queue.\n\n"
            f"Το Mac σου (αν είναι ανοιχτό) θα το αναλάβει αυτόματα σε λίγα δευτερόλεπτα!\n\n"
            f"🆔 `{video_id}`"
        )
        logger.info(f"Video {video_id} APPROVED — marked in database.")

    elif action == "publish":
        logger.info(f"Video {video_id} RENDER APPROVAL RECEIVED")
        send_message(chat_id,
            f"🎬 *Approved for Render!*\n\n"
            f"Το Orchestrator ξεκινάει το Remotion render (local).\n"
            f"🆔 `{video_id}`"
        )
        update_video_status(video_id, "awaiting_publish_approval")

    elif action == "reject":
        update_video_status(video_id, "failed", error_log="Rejected by user via Telegram")
        send_message(chat_id,
            f"❌ *Rejected & Regenerate.* Video marked for regeneration/failed.\n\n🆔 `{video_id}`"
        )
        logger.info(f"Video {video_id} REJECTED")


# ── Main poll loop ────────────────────────────────────────────────────────────

def run():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in .env")
        sys.exit(1)

    logger.info("🤖 Telegram bot started (long-poll mode)")
    logger.info(f"Chat ID: {CHAT_ID}")

    offset = None

    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
            if offset:
                params["offset"] = offset

            r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
            updates = r.json().get("result", [])

            for update in updates:
                offset = update["update_id"] + 1

                if "message" in update:
                    handle_message(update["message"])
                elif "callback_query" in update:
                    handle_callback(update["callback_query"])

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Poll error: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run()
