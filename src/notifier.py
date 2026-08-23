#!/usr/bin/env python3
"""
Telegram Notification Engine
Sends real-time pipeline status updates to a Telegram chat.
Used by all pipeline steps (orchestrator, publisher, etc.)

Credentials are read lazily at call time so this module works correctly
regardless of when it is imported relative to load_dotenv().
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _get_credentials():
    """Return (bot_token, chat_id) read from env at call time (lazy)."""
    return os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", "")


def _send(text: str, silent: bool = False) -> bool:
    """
    Internal helper — posts a message to Telegram.
    Returns True on success, False on failure (never raises).
    """
    bot_token, chat_id = _get_credentials()
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not configured. Skipping notification.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
        "disable_notification": silent,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        else:
            logger.error(f"Telegram API error {r.status_code}: {r.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False


# ──────────────────────────────────────────────
# Public notification functions
# ──────────────────────────────────────────────

def notify_pipeline_start(video_id: str, title: str):
    """Sent at the very beginning of a production run."""
    _send(
        f"🚀 *PIPELINE ΞΕΚΙΝΗΣΕ*\n\n"
        f"📌 *Τίτλος:* {title}\n"
        f"🆔 *ID:* `{video_id}`\n\n"
        f"⏳ Ξεκινά η αυτόματη παραγωγή βίντεο..."
    )


def notify_step_complete(video_id: str, step: str, details: str = "", silent: bool = False):
    """Sent after each step completes successfully."""
    detail_line = f"\n📊 {details}" if details else ""
    _send(
        f"✅ *{step}*{detail_line}\n"
        f"🆔 `{video_id}`",
        silent=silent
    )


def notify_step_failed(video_id: str, step: str, error: str):
    """Sent when a step fails (non-fatal — pipeline may continue)."""
    _send(
        f"⚠️ *{step} — ΑΠΟΤΥΧΙΑ*\n\n"
        f"🆔 `{video_id}`\n"
        f"🔴 `{error[:300]}`"
    )


def notify_render_complete(video_id: str, video_path: str, duration_hint: str = ""):
    """Sent after local Remotion render finishes."""
    dur = f" | ⏱ {duration_hint}" if duration_hint else ""
    _send(
        f"🎬 *RENDER ΟΛΟΚΛΗΡΩΘΗΚΕ*{dur}\n\n"
        f"🆔 `{video_id}`\n"
        f"📁 `{video_path}`\n\n"
        f"📤 Ξεκινά upload στο YouTube..."
    )


def notify_published(video_id: str, title: str, youtube_url: str):
    """Sent after a successful YouTube upload."""
    _send(
        f"🎉 *ΔΗΜΟΣΙΕΥΤΗΚΕ ΣΤΟ YOUTUBE!*\n\n"
        f"📌 *Τίτλος:* {title}\n"
        f"🆔 *Video ID:* `{video_id}`\n\n"
        f"▶️ [Άνοιγμα στο YouTube]({youtube_url})\n\n"
        f"✅ Το βίντεο είναι πλέον online!"
    )


def notify_pipeline_error(video_id: str, step: str, error: str):
    """Sent when the pipeline crashes with an unrecoverable error."""
    _send(
        f"❌ *PIPELINE CRASH*\n\n"
        f"🆔 `{video_id}`\n"
        f"💥 *Βήμα:* {step}\n"
        f"🔴 *Error:*\n`{error[:400]}`\n\n"
        f"Pipeline σταμάτησε. Έλεγξε τα logs."
    )

def notify_script_approval(video_id: str, title: str, hook_text: str, total_words: int, webhook_url: str):
    """Sent to request script approval via Telegram Inline Keyboard."""
    bot_token, chat_id = _get_credentials()
    if not bot_token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # We will use simple callback data or direct deep linking to a webhook if available.
    # Since the bot is running on Railway, it can listen to webhooks, but for now we just
    # send the buttons. The actual callback_query handling will be in the bot server.
    payload = {
        "chat_id": chat_id,
        "text": f"🛑 *ΕΓΚΡΙΣΗ SCRIPT ΑΠΑΙΤΕΙΤΑΙ*\n\n"
                f"📌 *Τίτλος:* {title}\n"
                f"📝 *Λέξεις:* {total_words}\n\n"
                f"🪝 *Hook:*\n_{hook_text}_\n\n"
                f"🆔 `{video_id}`",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve", "callback_data": f"approve:{video_id}"},
                    {"text": "❌ Reject", "callback_data": f"reject:{video_id}"}
                ]
            ]
        }
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception:
        pass

