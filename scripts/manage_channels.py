#!/usr/bin/env python3
"""
Monitored Channels Management CLI
Add, remove, and list competitor channels tracked by the Outlier Engine.
"""

import os
import sys
import argparse
import yt_dlp
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def get_client():
    if not SUPABASE_SERVICE_KEY:
        print("Error: SUPABASE_SERVICE_ROLE_KEY environment variable is required.")
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def extract_channel_metadata(channel_url: str):
    # Normalize to /videos tab to get proper metadata (plain channel URL returns limited data)
    normalized = channel_url.rstrip('/')
    if not normalized.endswith('/videos') and '/watch?' not in normalized:
        normalized = f"{normalized}/videos"

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'playlist_items': '1',  # Just need 1 entry for metadata
        'ignoreerrors': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(normalized, download=False)
        return {
            "channel_id": info.get('channel_id') or info.get('id') or channel_url,
            "channel_name": info.get('channel') or info.get('uploader') or info.get('title') or "Unknown Channel",
            "subscriber_count": info.get('channel_follower_count', 0) or 0
        }


def add_channel(url_or_handle: str):
    client = get_client()
    print(f"Fetching metadata for {url_or_handle}...")
    try:
        meta = extract_channel_metadata(url_or_handle)
        res = client.table("monitored_channels").upsert({
            "channel_id": meta["channel_id"],
            "channel_name": meta["channel_name"],
            "subscriber_count": meta["subscriber_count"]
        }, on_conflict="channel_id").execute()
        print(f"✅ Successfully added/updated: {meta['channel_name']} (ID: {meta['channel_id']}, Subs: {meta['subscriber_count']:,})")
    except Exception as e:
        print(f"❌ Failed to add channel: {e}")


def list_channels():
    client = get_client()
    res = client.table("monitored_channels").select("*").order("created_at", desc=True).execute()
    channels = res.data or []
    if not channels:
        print("No channels currently monitored.")
        return

    print(f"\n--- Monitored Channels ({len(channels)}) ---")
    print(f"{'Channel Name':<35} | {'Subscribers':<12} | {'Median Views':<12} | {'Channel ID'}")
    print("-" * 85)
    for ch in channels:
        subs = f"{ch.get('subscriber_count', 0):,}" if ch.get('subscriber_count') else "N/A"
        med = f"{ch.get('median_views', 0):,}" if ch.get('median_views') else "N/A"
        print(f"{ch.get('channel_name', ''):<35} | {subs:<12} | {med:<12} | {ch.get('channel_id')}")
    print("-" * 85 + "\n")


def remove_channel(channel_id: str):
    client = get_client()
    res = client.table("monitored_channels").delete().eq("channel_id", channel_id).execute()
    print(f"🗑️ Removed channel: {channel_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage monitored competitor YouTube channels.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    add_p = subparsers.add_parser("add", help="Add a channel by URL or handle")
    add_p.add_argument("url", help="YouTube Channel URL (e.g. https://www.youtube.com/@MagnatesMedia)")

    list_p = subparsers.add_parser("list", help="List all monitored channels")

    remove_p = subparsers.add_parser("remove", help="Remove a monitored channel by ID")
    remove_p.add_argument("channel_id", help="Channel ID to delete")

    args = parser.parse_args()

    if args.command == "add":
        add_channel(args.url)
    elif args.command == "list":
        list_channels()
    elif args.command == "remove":
        remove_channel(args.channel_id)
    else:
        parser.print_help()
