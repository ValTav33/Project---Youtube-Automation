#!/usr/bin/env python3
"""
Telegram Intake & Approval Bot
Allows sending a YouTube URL or custom topic prompt via Telegram to queue an approved video,
and handles review notifications with 1-click publish approval.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from supabase import create_client

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def get_supabase():
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is not configured.")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🎬 *YouTube Automation Engine Bot*\n\n"
        "Send me a topic, title, or YouTube video URL to immediately queue and approve a new documentary video production run.\n\n"
        "Commands:\n"
        "/queue - View current production queue\n"
        "/stats - View pipeline statistics\n"
        "/help - Help menu"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sb = get_supabase()
    res = sb.table("videos").select("id, target_title, status, created_at").order("created_at", desc=True).limit(8).execute()
    rows = res.data or []
    if not rows:
        await update.message.reply_text("Queue is currently empty.")
        return

    text = "📋 *Recent Production Queue:*\n\n"
    for r in rows:
        text += f"• *{r['target_title'][:40]}*\n  Status: `{r['status']}` | ID: `{r['id'][:8]}`\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return

    user = update.effective_user
    logger.info(f"Received manual intake from {user.username}: '{text}'")

    sb = get_supabase()
    # Insert new record directly with status 'approved' to trigger the pipeline
    res = sb.table("videos").insert({
        "source_type": "manual_telegram",
        "target_title": text[:120],
        "topic_premise": text,
        "status": "approved"
    }).execute()

    if res.data:
        v_id = res.data[0]["id"]
        reply = (
            f"✅ *Topic Approved & Queued for Production!*\n\n"
            f"📌 *Title / Premise:* {text}\n"
            f"🆔 *Video ID:* `{v_id}`\n"
            f"🚀 *Next Step:* GPT-4o Script Engine triggered."
        )
        await update.message.reply_text(reply, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Failed to create video entry in Supabase.")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split(":")
    action = parts[0]
    video_id = parts[1] if len(parts) > 1 else None

    if not video_id:
        return

    sb = get_supabase()

    if action == "publish":
        sb.table("videos").update({"status": "uploaded"}).eq("id", video_id).execute()
        await query.edit_message_text(f"🚀 *Video {video_id[:8]} Published to Public!*", parse_mode="Markdown")
    elif action == "reject":
        sb.table("videos").update({"status": "failed", "error_log": "Rejected by user via Telegram gate"}).eq("id", video_id).execute()
        await query.edit_message_text(f"❌ *Video {video_id[:8]} Rejected and marked as failed.*", parse_mode="Markdown")


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not configured in .env. Exiting.")
        sys.exit(1)

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("queue", queue_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("🤖 Telegram Intake & Approval Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
