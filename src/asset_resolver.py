#!/usr/bin/env python3
"""
Hybrid Visual Sourcing Engine
Slices scene queries and searches Pexels Video API for 1080p stock footage,
with automatic fallback to Fal.ai Flux Schnell generative AI images.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any, List, Optional
import aiohttp
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://wrowkhhwlvmigvyescdv.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


async def query_pexels_video(session: aiohttp.ClientSession, query: str) -> Optional[str]:
    """
    Queries Pexels Video API for HD landscape stock footage.
    """
    if not PEXELS_API_KEY:
        return None

    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "orientation": "landscape", "per_page": 5}

    try:
        async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                videos = data.get("videos", [])
                if videos:
                    video_files = videos[0].get("video_files", [])
                    # Pick 1080p HD file or first available
                    hd_file = next((f for f in video_files if f.get("width") == 1920 and f.get("height") == 1080), None)
                    if not hd_file and video_files:
                        hd_file = video_files[0]
                    if hd_file:
                        return hd_file.get("link")
    except Exception as e:
        logger.warning(f"Pexels query failed for '{query}': {e}")

    return None


async def generate_fal_flux_image(session: aiohttp.ClientSession, prompt: str) -> Optional[str]:
    """
    Generates high-contrast 4K documentary style image via Fal.ai Flux Schnell.
    """
    if not FAL_KEY:
        return None

    url = "https://queue.fal.run/fal-ai/flux/schnell"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": f"Cinematic 4K documentary b-roll, hyper-realistic, dramatic lighting, high contrast: {prompt}",
        "image_size": "landscape_16_9",
        "num_inference_steps": 4
    }

    try:
        async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status in (200, 201):
                data = await resp.json()
                images = data.get("images", [])
                if images:
                    return images[0].get("url")
    except Exception as e:
        logger.warning(f"Fal.ai generation failed for '{prompt}': {e}")

    return None


async def resolve_scene_asset(session: aiohttp.ClientSession, scene: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolves visual media for a single scene with stock video or AI image fallback.
    """
    scene_id = scene.get("scene_id", 0)
    query = scene.get("broll_search_query", "")
    layout = scene.get("layout_type", "STOCK_BROLL")

    # 1. Check Pexels Video
    video_url = await query_pexels_video(session, query)
    if video_url:
        logger.info(f"Scene #{scene_id}: Found Stock Video from Pexels for '{query}'")
        return {
            "scene_id": scene_id,
            "asset_type": "video",
            "asset_url": video_url
        }

    # 2. Fallback to Fal.ai Flux Image
    logger.info(f"Scene #{scene_id}: Falling back to Fal.ai Flux for '{query}'")
    image_url = await generate_fal_flux_image(session, query)
    if image_url:
        return {
            "scene_id": scene_id,
            "asset_type": "image",
            "asset_url": image_url
        }

    # 3. Default fallback placeholder if offline
    return {
        "scene_id": scene_id,
        "asset_type": "image",
        "asset_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1920&q=80"
    }


async def resolve_all_scene_assets(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Resolves assets for all scenes concurrently.
    """
    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [resolve_scene_asset(session, s) for s in scenes]
        resolved = await asyncio.gather(*tasks)

    # Merge resolved asset data back into scenes
    asset_map = {r["scene_id"]: r for r in resolved}
    for scene in scenes:
        s_id = scene.get("scene_id")
        if s_id in asset_map:
            scene["asset_type"] = asset_map[s_id]["asset_type"]
            scene["asset_url"] = asset_map[s_id]["asset_url"]

    return scenes


from stage_runner import PipelineStage
from contracts import SceneIntentPlan, AssetManifest, Asset

class AssetResolutionStage(PipelineStage):
    """
    Pulls scripted scenes, resolves assets for each scene using async fetching, 
    and outputs an AssetManifest artifact.
    """
    name = "asset_resolution"
    output_type = "AssetManifest"

    def execute(self, inputs: Dict[str, Any]) -> AssetManifest:
        intent_plan: SceneIntentPlan = inputs.get("scene_intent")
        if not intent_plan:
            raise ValueError("Missing scene_intent input")
            
        logger.info(f"[{self.name}] Resolving visual assets for {len(intent_plan.scenes)} scenes in video {self.video_id}...")
        
        # Convert scenes to dict format expected by the async functions
        scenes_data = [{"scene_id": s.scene_id, "broll_search_query": s.broll_search_query} for s in intent_plan.scenes]
        
        try:
            resolved_data = asyncio.run(resolve_all_scene_assets(scenes_data))
            
            assets = []
            for item in resolved_data:
                provider = "pexels" if item.get("asset_type") == "video" else "fal.ai"
                if "unsplash" in item.get("asset_url", ""):
                    provider = "unsplash"
                    
                assets.append(Asset(
                    asset_id=f"asset_{item['scene_id']}",
                    scene_id=item["scene_id"],
                    asset_type=item["asset_type"],
                    asset_url=item["asset_url"],
                    provider=provider
                ))
                
            manifest = AssetManifest(
                artifact_id=f"assets-{self.video_id}",
                video_id=self.video_id,
                assets=assets
            )
            manifest.parent_artifact_ids = [intent_plan.artifact_id]
            return manifest
            
        except Exception as e:
            logger.error(f"[{self.name}] Asset resolution failed: {e}")
            raise RuntimeError(f"Asset resolution failed: {e}")

if __name__ == "__main__":
    print("This module provides AssetResolutionStage and should be run via the orchestrator.")
