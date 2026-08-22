import os
import logging
import asyncio
import aiohttp
from typing import Dict, Any

from stage_runner import PipelineStage
from contracts import ShotPlan, SceneIntentPlan, AssetManifest, Asset
from asset_resolver import query_pexels_video, generate_fal_flux_image

logger = logging.getLogger(__name__)

class AssetStage(PipelineStage):
    """
    Resolves actual media files for the visual shots.
    """
    name = "asset_resolution"
    output_type = "AssetManifest"

    async def _resolve_assets_async(self, intent: SceneIntentPlan, shots: ShotPlan) -> AssetManifest:
        connector = aiohttp.TCPConnector(limit=5)
        assets = []
        
        # Build mapping of scene_id to query
        queries = {scene.scene_id: scene.broll_search_query for scene in intent.scenes}
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            # For each unique scene, we need one asset
            for scene in intent.scenes:
                scene_id = scene.scene_id
                query = scene.broll_search_query
                sfx = getattr(scene, 'sfx_query', None)
                tasks.append(self._resolve_single(session, scene_id, query, sfx))
                
            resolved_results = await asyncio.gather(*tasks)
            
            for res in resolved_results:
                if res:
                    assets.append(res)
                    
        manifest = AssetManifest(
            artifact_id=f"manifest-{self.video_id}",
            video_id=self.video_id,
            assets=assets
        )
        return manifest

    async def _resolve_single(self, session, scene_id, query, sfx_query=None) -> Asset:
        sfx_url = None
        if sfx_query:
            lower = sfx_query.lower()
            if "whoosh" in lower:
                sfx_url = "https://cdn.pixabay.com/audio/2022/03/15/audio_24e073cda2.mp3"
            elif "cash" in lower or "money" in lower:
                sfx_url = "https://cdn.pixabay.com/audio/2021/08/04/audio_3d19114757.mp3"
            elif "boom" in lower:
                sfx_url = "https://cdn.pixabay.com/audio/2022/03/10/audio_51795c6f60.mp3"
            elif "glitch" in lower:
                sfx_url = "https://cdn.pixabay.com/audio/2021/08/09/audio_9ef062d295.mp3"
            else:
                sfx_url = "https://cdn.pixabay.com/audio/2022/03/15/audio_24e073cda2.mp3"

        if os.getenv("MOCK_EXTERNAL_APIS") == "true":
            return Asset(
                asset_id=f"ast_{scene_id}",
                scene_id=scene_id,
                asset_type="image",
                asset_url="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1920&q=80",
                sfx_url=sfx_url,
                provider="mock"
            )
            
        # 1. Check Pexels
        video_url = await query_pexels_video(session, query)
        if video_url:
            return Asset(
                asset_id=f"ast_{scene_id}",
                scene_id=scene_id,
                asset_type="video",
                asset_url=video_url,
                sfx_url=sfx_url,
                provider="pexels"
            )
            
        # 2. Fallback to Fal.ai
        image_url = await generate_fal_flux_image(session, query)
        if image_url:
            return Asset(
                asset_id=f"ast_{scene_id}",
                scene_id=scene_id,
                asset_type="image",
                asset_url=image_url,
                sfx_url=sfx_url,
                provider="fal"
            )
            
        # 3. Default fallback
        return Asset(
            asset_id=f"ast_{scene_id}",
            scene_id=scene_id,
            asset_type="image",
            asset_url="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1920&q=80",
            provider="fallback"
        )

    def execute(self, inputs: Dict[str, Any]) -> AssetManifest:
        intent_raw = inputs.get("scene_intent")
        shot_plan_raw = inputs.get("shot_plan")
        
        if not intent_raw or not shot_plan_raw:
            raise ValueError("Missing scene_intent or shot_plan")
            
        intent = SceneIntentPlan.model_validate(intent_raw) if isinstance(intent_raw, dict) else intent_raw
        shot_plan = ShotPlan.model_validate(shot_plan_raw) if isinstance(shot_plan_raw, dict) else shot_plan_raw
            
        manifest = asyncio.run(self._resolve_assets_async(intent, shot_plan))
        manifest.parent_artifact_ids = [intent.artifact_id, shot_plan.artifact_id]
        
        return manifest
