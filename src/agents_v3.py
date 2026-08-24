import json
import logging
from typing import Dict, Any, List
import uuid

import openai
from openai import OpenAI
from pydantic import BaseModel

from contracts_v3 import (
    ChannelCreativeBible,
    VideoBrief,
    VerifiedResearchPacket,
    VerifiedClaim,
    StoryBlueprint,
    VisualBriefPlan,
    VisualBeat,
    VisualComponentChoice,
    AssetManifest,
    ResolvedAsset,
    AudioPlan
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
    def generate_brief(self, video_id: str, topic: str) -> VideoBrief:
        system = (
            "You are a master YouTube strategist. Your job is to take a raw topic and "
            "turn it into a highly optimized VideoBrief."
        )
        prompt = f"Topic: {topic}\n\nGenerate the VideoBrief. Target duration should be around 180 seconds. video_id is {video_id}."
        
        brief: VideoBrief = self._generate_structured(prompt, system, VideoBrief)
        # Force overrides for safety
        brief.video_id = video_id
        brief.artifact_id = f"br-{uuid.uuid4().hex[:8]}"
        return brief

class MockResearchAgent(BaseV3Agent):
    """Mocks the research process to guarantee high quality inputs for pipeline testing."""
    def run_research(self, video_id: str, brief: VideoBrief) -> VerifiedResearchPacket:
        logger.info("Running mocked research...")
        return VerifiedResearchPacket(
            artifact_id=f"rp-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            claims=[
                VerifiedClaim(
                    claim_id="cl-1",
                    claim_text="AI agents could automate 30% of coding tasks by 2028.",
                    source_url="https://example.com/ai-report",
                    publisher="Global Tech Report",
                    publication_date="2026-01-01",
                    evidence_note="Based on surveyed engineering leaders.",
                    confidence="high"
                ),
                VerifiedClaim(
                    claim_id="cl-2",
                    claim_text="The economic impact of AI automation could exceed $1 Trillion annually.",
                    source_url="https://example.com/econ-impact",
                    publisher="Economic Institute",
                    publication_date="2026-02-15",
                    evidence_note="Calculated via productivity gains.",
                    confidence="high"
                )
            ]
        )

class StoryAgent(BaseV3Agent):
    def draft_story(self, video_id: str, brief: VideoBrief, research: VerifiedResearchPacket) -> StoryBlueprint:
        system = (
            "You are a master storyteller. Draft a narrative script (StoryBlueprint) based on the VideoBrief "
            "and VerifiedResearchPacket. Create structural beats. You MUST cite claim_ids when you use facts."
        )
        
        prompt = (
            f"Brief: {brief.model_dump_json(indent=2)}\n\n"
            f"Research: {research.model_dump_json(indent=2)}\n\n"
            "Draft the StoryBlueprint."
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
            "For cited claims, use EvidenceCard. Every beat must have exactly one VisualBeat matching its beat_id."
        )
        
        prompt = f"Story: {story.model_dump_json(indent=2)}\n\nCreate the VisualBriefPlan."
        
        plan: VisualBriefPlan = self._generate_structured(prompt, system, VisualBriefPlan)
        plan.video_id = video_id
        plan.artifact_id = f"vb-{uuid.uuid4().hex[:8]}"
        return plan

class MockAssetCuratorAgent(BaseV3Agent):
    """Mocks the asset curation process by assigning high-quality Unsplash/Pexels URLs to shots that need them."""
    def resolve_assets(self, video_id: str, visual_plan: VisualBriefPlan) -> AssetManifest:
        logger.info("Resolving mocked assets...")
        resolved = []
        for beat in visual_plan.visual_beats:
            if beat.component_choice.component_type in ["CinematicMedia", "ProductScreen"]:
                # Mock a static high quality tech image for now
                url = "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=1920&auto=format&fit=crop"
                resolved.append(
                    ResolvedAsset(
                        beat_id=beat.beat_id,
                        asset_url=url,
                        provider="Unsplash",
                        license_category="mocked"
                    )
                )
        
        return AssetManifest(
            artifact_id=f"am-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            resolved_assets=resolved
        )

class MockAudioDirectorAgent(BaseV3Agent):
    """Mocks the audio planning process, assigning a backing track and mock TTS audio cues."""
    def plan_audio(self, video_id: str, story: StoryBlueprint, visual_plan: VisualBriefPlan) -> AudioPlan:
        logger.info("Planning mocked audio...")
        # Since we do not have actual TTS output mapped to frames yet, we just provide a mock track
        # in reality we'd synthesize audio here and get exact durations.
        # But this agent at least creates the AudioPlan contract.
        return AudioPlan(
            artifact_id=f"ap-{uuid.uuid4().hex[:8]}",
            video_id=video_id,
            music_track_url="https://example.com/mock-lofi-beat.mp3",
            sfx_cues=[
                {"beat_id": story.beats[0].beat_id, "sfx_type": "whoosh"}
            ]
        )

