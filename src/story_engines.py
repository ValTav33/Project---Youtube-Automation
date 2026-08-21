import os
import logging
from typing import Dict, Any
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

from stage_runner import PipelineStage
from contracts import (
    PromiseContract,
    ResearchPacket,
    HookScript,
    StoryScript,
    EditedStoryScript
)

load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class BaseOpenAIStage(PipelineStage):
    """Base class for stages that use OpenAI structured outputs."""
    
    def __init__(self, sb, video_id):
        super().__init__(sb, video_id)
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
    def generate_structured(self, system_prompt: str, user_prompt: str, response_format: type[BaseModel]) -> BaseModel:
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=response_format,
            temperature=0.7,
            max_tokens=6000
        )
        return response.choices[0].message.parsed


class PromiseStage(BaseOpenAIStage):
    name = "promise_generation"
    output_type = "PromiseContract"

    def execute(self, inputs: Dict[str, Any]) -> PromiseContract:
        topic = inputs.get("target_title", "Unknown Topic")
        premise = inputs.get("topic_premise", "")
        
        system = "You are a master YouTube strategist. Define the core viewer promise, emotional hook, and primary claim for a documentary video."
        user = f"Topic: {topic}\nContext: {premise}\nGenerate a high-converting Promise Contract."
        
        parsed = self.generate_structured(system, user, PromiseContract)
        parsed.artifact_id = f"promise-{self.video_id}"
        parsed.video_id = self.video_id
        return parsed


class ResearchStage(BaseOpenAIStage):
    name = "research_generation"
    output_type = "ResearchPacket"
    
    def execute(self, inputs: Dict[str, Any]) -> ResearchPacket:
        promise: PromiseContract = inputs.get("promise_contract")
        if not promise:
            raise ValueError("Missing promise_contract input")
            
        system = "You are a lead researcher. Generate factual grounding and constraints for the documentary based on the core promise."
        user = f"Claim: {promise.primary_claim}\nTopic: {promise.target_title}\nProvide verified facts and statistics."
        
        parsed = self.generate_structured(system, user, ResearchPacket)
        parsed.artifact_id = f"research-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [promise.artifact_id]
        return parsed


class HookStage(BaseOpenAIStage):
    name = "hook_generation"
    output_type = "HookScript"
    
    def execute(self, inputs: Dict[str, Any]) -> HookScript:
        promise: PromiseContract = inputs.get("promise_contract")
        research: ResearchPacket = inputs.get("research_packet")
        
        if not promise or not research:
            raise ValueError("Missing inputs for HookStage")
            
        system = (
            "You are a YouTube hook specialist. Write the first 3 scenes of the script. "
            "Drop the viewer immediately into a high-stakes moment or shocking contradiction. "
            "Do not introduce the channel. Exactly 3 beats."
        )
        user = f"Promise: {promise.hook_promise}\nFacts: {[f.claim for f in research.facts[:3]]}\nWrite the hook."
        
        parsed = self.generate_structured(system, user, HookScript)
        parsed.artifact_id = f"hook-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [promise.artifact_id, research.artifact_id]
        
        # Calculate total word count
        parsed.total_word_count = sum(b.word_count for b in parsed.beats)
        return parsed


class StoryStage(BaseOpenAIStage):
    name = "story_generation"
    output_type = "StoryScript"
    
    def execute(self, inputs: Dict[str, Any]) -> StoryScript:
        promise: PromiseContract = inputs.get("promise_contract")
        research: ResearchPacket = inputs.get("research_packet")
        hook: HookScript = inputs.get("hook_script")
        
        system = (
            "You are a master scriptwriter. Write scenes 4 through 40 of the documentary. "
            "Ensure escalation, reveals, and a satisfying payoff. Each narration must be 30-45 words. "
            "Maintain the tone and continue directly from the provided hook."
        )
        
        hook_text = "\\n".join([b.narration for b in hook.beats])
        user = f"Promise: {promise.primary_claim}\nResearch: {[f.claim for f in research.facts]}\nHook (Already Written):\n{hook_text}\nGenerate the remaining 37 scenes."
        
        parsed = self.generate_structured(system, user, StoryScript)
        
        # Prepend the hook beats to the story beats
        full_beats = hook.beats + parsed.beats
        parsed.beats = full_beats
        parsed.total_word_count = sum(b.word_count for b in full_beats)
        
        parsed.artifact_id = f"story-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [hook.artifact_id, promise.artifact_id, research.artifact_id]
        return parsed


class RetentionEditorStage(BaseOpenAIStage):
    name = "retention_editing"
    output_type = "EditedStoryScript"
    
    def execute(self, inputs: Dict[str, Any]) -> EditedStoryScript:
        story: StoryScript = inputs.get("story_script")
        if not story:
            raise ValueError("Missing story_script")
            
        system = (
            "You are a brutal retention editor. Review the provided script. "
            "Eliminate boring exposition. Ensure pacing is fast and open loops are paid off. "
            "Return the full edited 40-scene script."
        )
        
        script_text = "\\n".join([f"[{b.beat_id}] {b.narration}" for b in story.beats])
        user = f"Edit this script for retention:\n\n{script_text}"
        
        parsed = self.generate_structured(system, user, EditedStoryScript)
        parsed.artifact_id = f"edited-story-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [story.artifact_id]
        parsed.total_word_count = sum(b.word_count for b in parsed.beats)
        return parsed
