import json
import logging
import os
import requests
from typing import Dict, Any, List, Optional
import uuid

import openai
from openai import OpenAI
from pydantic import BaseModel

from contracts_v3 import (
    ChannelCreativeBible,
    VideoBrief,
    ThumbnailPlan,
    VerifiedResearchPacket,
    VerifiedClaim,
    StoryBlueprint,
    VisualBriefPlan,
    VisualBeat,
    VisualComponentChoice,
    AssetManifest,
    ResolvedAsset,
    AudioPlan,
    ProductionManifest,
    EditorRepairPlan,
    RepairRequest
)

logger = logging.getLogger(__name__)

class BaseV3Agent:
    def __init__(self):
        self.client = OpenAI() # Expects OPENAI_API_KEY in env

    def _generate_structured(self, prompt: str, system_prompt: str, response_model: type[BaseModel]) -> BaseModel:
        """Helper to invoke OpenAI with structured outputs (JSON schema matching Pydantic)."""
        logger.info(f"Invoking LLM for {response_model.__name__}...")
        
        # We use standard chat completions with JSON schema function calling / structured outputs.
        # For simplicity in this implementation, we use the instructor-like pattern 
        # or just standard openai parsing if using openai >= 1.40 (Structured Outputs).
        # We will use the new beta `client.beta.chat.completions.parse` method.
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_model
            )
            return response.choices[0].message.parsed
        except Exception as e:
            logger.error(f"Failed to generate structured output: {e}")
            raise

class StrategyAgent(BaseV3Agent):
    """Generates the initial video brief from a topic."""
    def generate_brief(self, video_id: str, topic: str, target_duration_seconds: int = 600) -> VideoBrief:
        logger.info(f"Generating VideoBrief for {target_duration_seconds}s...")
        system = "You are an elite YouTube strategist. Output ONLY valid JSON matching the schema."
        prompt = f"Create a viral documentary-style video brief for the topic: '{topic}'. The target video duration is exactly {target_duration_seconds} seconds. Ensure the pacing and promise are suited for this length."
        
        brief: VideoBrief = self._generate_structured(prompt, system, VideoBrief)
        brief.video_id = video_id
        brief.target_duration_seconds = target_duration_seconds
        brief.artifact_id = f"vb-{uuid.uuid4().hex[:8]}"
        return brief

class ThumbnailAgent(BaseV3Agent):
    """Generates a DALL-E 3 thumbnail based on the VideoBrief's thumbnail hypothesis."""
    def generate_thumbnail(self, video_id: str, brief: VideoBrief) -> ThumbnailPlan:
        logger.info("Generating optimized thumbnail prompt...")
        system = "You are an AI image prompt engineering expert. Translate the thumbnail concept into a highly detailed, optimized prompt for an image generation model like DALL-E 3. Focus on cinematic lighting, high contrast, and youtube aesthetic."
        user = f"Concept: {brief.thumbnail_hypothesis}\nWrite the exact image prompt."
        
        plan: ThumbnailPlan = self._generate_structured(user, system, ThumbnailPlan)
        plan.video_id = video_id
        plan.artifact_id = f"tp-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Generating DALL-E image with prompt: {plan.optimized_image_prompt}")
        if os.getenv("MOCK_EXTERNAL_APIS", "false") == "true":
            logger.info("MOCK_EXTERNAL_APIS=true: Bypassing DALL-E 2/3")
            plan.generated_url = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1920&auto=format&fit=crop"
            return plan

        try:
            response = self.client.images.generate(
                model="dall-e-2",
                prompt=plan.optimized_image_prompt + " (Must be a highly professional YouTube documentary thumbnail without any text or words).",
                size="1024x1024",
                n=1,
            )
            image_url = response.data[0].url
            plan.generated_url = image_url
            logger.info(f"Generated Thumbnail URL: {image_url}")
        except Exception as e:
            logger.error(f"Failed to generate DALL-E 3 thumbnail: {e}")
            
        return plan

class ResearchAgent(BaseV3Agent):
    """Generates dynamically verified research claims using GPT-4o."""
    def run_research(self, video_id: str, brief: VideoBrief) -> VerifiedResearchPacket:
        logger.info("Generating dynamic research claims via Perplexity...")
        system = (
            "You are an elite researcher. Based on the topic and brief, generate 3-5 verified facts. "
            "Because you have internet access, use real, verified sources. "
            "You MUST output ONLY a raw JSON object matching this schema exactly, and nothing else. "
            "Do not wrap it in markdown block quotes (```json).\n"
            f"{VerifiedResearchPacket.model_json_schema()}"
        )
        user = f"Topic: {brief.topic}\nPromise: {brief.promise}\nTension: {brief.audience_tension}\nGenerate the VerifiedResearchPacket JSON."
        
        perp_key = os.getenv("PERPLEXITY_API_KEY")
        if not perp_key:
            logger.warning("No PERPLEXITY_API_KEY found, falling back to OpenAI.")
            packet: VerifiedResearchPacket = self._generate_structured(user, system, VerifiedResearchPacket)
            packet.video_id = video_id
            packet.artifact_id = f"vr-{uuid.uuid4().hex[:8]}"
            return packet

        try:
            import openai
            import json
            perp_client = openai.Client(api_key=perp_key, base_url="https://api.perplexity.ai")
            response = perp_client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )
            raw_text = response.choices[0].message.content.strip()
            # clean up markdown backticks if they exist
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            
            data = json.loads(raw_text.strip())
            packet = VerifiedResearchPacket(**data)
            
        except Exception as e:
            logger.error(f"Perplexity failed, using fallback data. Error: {e}")
            from contracts_v3 import VerifiedClaim
            packet = VerifiedResearchPacket(
                claims=[VerifiedClaim(claim_id="c1", fact="Quantum computers use qubits", source_url="https://en.wikipedia.org/wiki/Quantum_computing", confidence_score=0.9)]
            )

        packet.video_id = video_id
        packet.artifact_id = f"vr-{uuid.uuid4().hex[:8]}"
        return packet

class StoryAgent(BaseV3Agent):
    def draft_story(self, video_id: str, brief: VideoBrief, research: VerifiedResearchPacket) -> StoryBlueprint:
        # Assuming ~150 words per minute (2.5 words per second)
        target_words = int(getattr(brief, "target_duration_seconds", 180) * 2.5)
        
        system = (
            "You are a master storyteller. Draft a narrative script (StoryBlueprint) based on the VideoBrief "
            "and VerifiedResearchPacket. Create structural beats. You MUST cite claim_ids when you use facts.\n"
            f"CRITICAL INSTRUCTION: Your target word count for the entire narration is approximately {target_words} words. "
            "Pace the story with depth, detailed analysis, and rich narrative to hit this target organically. "
            "Do not output a shallow summary; dive deep."
        )
        
        prompt = (
            f"Brief: {brief.model_dump_json(indent=2)}\n\n"
            f"Research: {research.model_dump_json(indent=2)}\n\n"
            f"Draft the StoryBlueprint aiming for ~{target_words} total words across all narrative beats."
        )
        
        blueprint: StoryBlueprint = self._generate_structured(prompt, system, StoryBlueprint)
        blueprint.video_id = video_id
        blueprint.artifact_id = f"sb-{uuid.uuid4().hex[:8]}"
        return blueprint

class VisualDirectorAgent(BaseV3Agent):
    def assign_visuals(self, video_id: str, story: StoryBlueprint) -> VisualBriefPlan:
        system = (
            "You are a visual director. Map visual components to each NarrativeBeat. "
            "Allowed components: CinematicMedia, EvidenceCard, BigNumber, DataChart, Timeline, Comparison, ProductScreen, TypographyImpact. "
            "For quantitative claims, use BigNumber or DataChart. For bold statements, use TypographyImpact. "
            "For cited claims, use EvidenceCard. Every beat must have exactly one VisualBeat matching its beat_id.\n"
            "CRITICAL INSTRUCTION: For long-form videos, do not rapidly alternate UI components (like BigNumber or EvidenceCard) constantly. "
            "Rely predominantly on CinematicMedia to pace the video, using UI components only to emphasize key facts, data, or transitions."
        )
        
        prompt = f"Story: {story.model_dump_json(indent=2)}\n\nCreate the VisualBriefPlan."
        
        plan: VisualBriefPlan = self._generate_structured(prompt, system, VisualBriefPlan)
        plan.video_id = video_id
        plan.artifact_id = f"vb-{uuid.uuid4().hex[:8]}"
        return plan

class AssetCuratorAgent(BaseV3Agent):
    """Curates assets by searching Pexels for relevant stock footage."""
    def resolve_assets(self, video_id: str, visual_plan: VisualBriefPlan, repair_plan: Optional[EditorRepairPlan] = None) -> AssetManifest:
        logger.info("Resolving assets via Pexels API...")
        resolved = []
        
        repair_beats = {}
        if repair_plan:
            for r in repair_plan.repairs:
                if r.issue_type == "asset_replacement":
                    repair_beats[r.beat_id] = r
                    
        pexels_key = os.getenv("PEXELS_API_KEY", "")
        headers = {"Authorization": pexels_key} if pexels_key else {}
        
        for beat in visual_plan.visual_beats:
            if beat.component_choice.component_type in ["CinematicMedia", "ProductScreen"]:
                
                # Use a default stock photo fallback
                url = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1920&auto=format&fit=crop"
                provider = "Unsplash (Mock Fallback)"
                
                query = beat.component_choice.asset_query or beat.visual_argument or "technology abstract"
                
                if beat.beat_id in repair_beats:
                    logger.info(f"Applying asset repair to beat {beat.beat_id}")
                    # Use the repair description to find a better asset
                    query = repair_beats[beat.beat_id].description
                
                if pexels_key and os.getenv("MOCK_EXTERNAL_APIS", "false") != "true":
                    try:
                        logger.info(f"Querying Pexels for: {query}")
                        resp = requests.get(
                            "https://api.pexels.com/videos/search",
                            headers=headers,
                            params={"query": query, "orientation": "landscape", "per_page": 5},
                            timeout=10
                        )
                        if resp.status_code == 200:
                            videos = resp.json().get("videos", [])
                            if videos:
                                video_files = videos[0].get("video_files", [])
                                hd_file = next((f for f in video_files if f.get("width") == 1920 and f.get("height") == 1080), None)
                                if not hd_file and video_files:
                                    hd_file = video_files[0]
                                if hd_file and hd_file.get("link"):
                                    url = hd_file["link"]
                                    provider = "Pexels"
                    except Exception as e:
                        logger.error(f"Failed to query Pexels: {e}")
                
                if beat.beat_id in repair_beats and provider == "Unsplash (Mock Fallback)":
                    url = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1920&auto=format&fit=crop" # Repaired static fallback
                    provider = "Unsplash (Repaired Fallback)"

                resolved.append(
                    ResolvedAsset(
                        beat_id=beat.beat_id,
                        asset_url=url,
                        provider=provider,
                        license_category="stock" if provider == "Pexels" else "mocked"
                    )
                )
        
        return AssetManifest(
            artifact_id=f"am-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            resolved_assets=resolved
        )

class AudioDirectorAgent(BaseV3Agent):
    """Plans the audio, and synthesizes the narration via ElevenLabs API."""
    def plan_audio(self, video_id: str, story: StoryBlueprint, visual_plan: VisualBriefPlan) -> AudioPlan:
        logger.info("Synthesizing audio via ElevenLabs...")
        
        # Combine all narration
        full_narration = " ".join([beat.narration_text for beat in story.beats])
        
        # We will use the existing audio_generator.py logic
        import audio_generator
        
        audio_url = None
        duration_seconds = max(3.0, len(full_narration.split()) / 2.5) # Default fallback duration
        
        if os.getenv("ELEVENLABS_API_KEY") and os.getenv("MOCK_EXTERNAL_APIS", "false") != "true":
            try:
                # audio_bytes, raw_words, duration = audio_generator.generate_speech_with_timestamps(full_narration)
                # For simplicity in V3 (without Supabase upload here for now), we just simulate the exact duration 
                # or actually call it. Let's call it.
                audio_bytes, raw_words, duration = audio_generator.generate_speech_with_timestamps(full_narration)
                duration_seconds = duration
                
                # We upload it to Supabase (assuming supabase client is set up, else we save locally)
                # For now, let's just log it and rely on the frontend to play it if uploaded.
                # If Supabase is configured:
                if os.getenv("SUPABASE_URL"):
                    from supabase import create_client
                    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
                    file_path = f"{video_id}.mp3"
                    sb.storage.from_("audio").upload(
                        path=file_path,
                        file=audio_bytes,
                        file_options={"content-type": "audio/mpeg", "upsert": "true"}
                    )
                    public_url = sb.storage.from_("audio").get_public_url(file_path)
                    audio_url = public_url if isinstance(public_url, str) else public_url.get("publicUrl", "")
            except Exception as e:
                logger.error(f"ElevenLabs generation failed: {e}")
        else:
            logger.info("ElevenLabs bypassed. Mocking audio duration.")
        
        sfx_cues = []
        # Assign a whoosh to the first cinematic transition
        for beat in visual_plan.visual_beats:
            if beat.component_choice.component_type == "CinematicMedia":
                sfx_cues.append({"beat_id": beat.beat_id, "sfx_type": "whoosh"})
                break
                
        return AudioPlan(
            artifact_id=f"ap-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            music_track_url="https://assets.mixkit.co/music/preview/mixkit-tech-house-vibes-130.mp3",
            voice_track_url=audio_url,
            total_duration_seconds=duration_seconds,
            sfx_cues=sfx_cues
        )

class MockQAAgent(BaseV3Agent):
    """Mocks the QA / Review process. Will always suggest replacing the first asset it finds."""
    def run_qa(self, video_id: str, manifest: ProductionManifest, visual_plan: VisualBriefPlan) -> EditorRepairPlan:
        logger.info("Running mocked QA...")
        
        # Find the first beat that had an asset
        repairs = []
        for beat in visual_plan.visual_beats:
            if beat.component_choice.component_type in ["CinematicMedia", "ProductScreen"]:
                repairs.append(
                    RepairRequest(
                        beat_id=beat.beat_id,
                        issue_type="asset_replacement",
                        description="Asset feels too generic. Please find a more specific, high-tech abstract background."
                    )
                )
                break # Just request one repair for the mock test
                
        return EditorRepairPlan(
            artifact_id=f"erp-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            target_manifest_id=manifest.artifact_id,
            repairs=repairs
        )

