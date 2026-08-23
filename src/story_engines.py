import os
import logging
from typing import Dict, Any
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

from stage_runner import PipelineStage
from contracts import (
    ResearchPacket,
    AngleStrategy,
    MarketingStrategy,
    ThumbnailPromptPlan,
    StoryBeatPlan,
    StoryScript,
    CriticReview,
    EditedStoryScript,
    QualityScoreReport
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
            model="gpt-5.6-luna",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=response_format,
            temperature=1,
            max_completion_tokens=8000
        )
        return response.choices[0].message.parsed


class ResearchAgentStage(BaseOpenAIStage):
    name = "research_agent"
    output_type = "ResearchPacket"
    
    def execute(self, inputs: Dict[str, Any]) -> ResearchPacket:
        topic = inputs.get("target_title", "Unknown Topic")
        
        system = "You are a master researcher. Gather highly engaging, verified facts, statistics, and narrative constraints for a YouTube documentary."
        user = f"Topic: {topic}\nProvide fascinating verified facts and key statistics that would make a great video."
        
        parsed = self.generate_structured(system, user, ResearchPacket)
        parsed.artifact_id = f"research-{self.video_id}"
        parsed.video_id = self.video_id
        return parsed


class AngleSelectorStage(BaseOpenAIStage):
    name = "angle_selector"
    output_type = "AngleStrategy"

    def execute(self, inputs: Dict[str, Any]) -> AngleStrategy:
        topic = inputs.get("target_title", "Unknown Topic")
        research: ResearchPacket = inputs.get("research_packet")
        
        if not research:
            raise ValueError("Missing research_packet input")
            
        system = "You are an expert YouTube strategist. Choose the most compelling, high-retention angle and target emotion based on the raw facts."
        user = f"Topic: {topic}\nFacts: {[f.claim for f in research.facts]}\nDefine the core angle and emotion."
        
        parsed = self.generate_structured(system, user, AngleStrategy)
        parsed.artifact_id = f"angle-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [research.artifact_id]
        return parsed


class MarketingStrategistStage(BaseOpenAIStage):
    name = "marketing_strategist"
    output_type = "MarketingStrategy"

    def execute(self, inputs: Dict[str, Any]) -> MarketingStrategy:
        angle: AngleStrategy = inputs.get("angle_strategy")
        global_feedback = inputs.get("global_feedback")
        
        if not angle:
            raise ValueError("Missing angle_strategy input")
            
        system = (
            "You are an elite YouTube marketer. First, generate 5 distinct hook ideas (Curiosity, Shocking Stat, Mystery, Controversial, Narrative). "
            "Score them out of 10 for retention tension, and select the highest scoring one as the 'hook_concept'. "
            "Then, formulate Title ideas and a Thumbnail visual concept that all interconnect to make an irresistible promise."
        )
        
        if global_feedback:
            learnings = "\n".join(global_feedback.get("hook_learnings", []) if isinstance(global_feedback, dict) else global_feedback.hook_learnings)
            meta = global_feedback.get("current_channel_meta", "") if isinstance(global_feedback, dict) else global_feedback.current_channel_meta
            system += f"\n\nHISTORICAL PERFORMANCE FEEDBACK:\n{learnings}\nCurrent Meta: {meta}\nUse this feedback to choose the best hook and title strategy."

        user = f"Angle: {angle.core_angle}\nEmotion: {angle.primary_emotion}\nGenerate the marketing strategy."
        
        parsed = self.generate_structured(system, user, MarketingStrategy)
        parsed.artifact_id = f"marketing-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [angle.artifact_id]
        return parsed


class ThumbnailPromptCreatorStage(BaseOpenAIStage):
    name = "thumbnail_prompt_creator"
    output_type = "ThumbnailPromptPlan"

    def execute(self, inputs: Dict[str, Any]) -> ThumbnailPromptPlan:
        strategy: MarketingStrategy = inputs.get("marketing_strategy")
        
        if not strategy:
            raise ValueError("Missing marketing_strategy input")
            
        system = "You are an AI image prompt engineering expert. Translate the thumbnail concept into a highly detailed, optimized prompt for an image generation model (like GPT-Image-2). Focus on cinematic lighting, high contrast, and youtube aesthetic."
        user = f"Concept: {strategy.thumbnail_concept}\nWrite the exact image prompt."
        
        parsed = self.generate_structured(system, user, ThumbnailPromptPlan)
        parsed.artifact_id = f"thumb-prompt-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [strategy.artifact_id]
        return parsed


class StoryArchitectStage(BaseOpenAIStage):
    name = "story_architect"
    output_type = "StoryBeatPlan"

    def execute(self, inputs: Dict[str, Any]) -> StoryBeatPlan:
        strategy: MarketingStrategy = inputs.get("marketing_strategy")
        research: ResearchPacket = inputs.get("research_packet")
        
        if not strategy or not research:
            raise ValueError("Missing inputs for StoryArchitectStage")
            
        system = (
            "You are a structural narrative architect. Design the pacing and beats for a 6-scene micro-documentary (approx 1 minute total) without writing the actual narration. "
            "You MUST follow this exact structure: HOOK -> QUESTION -> ESCALATION -> REVEAL -> CONSEQUENCE -> PAYOFF. "
            "You MUST enforce a Pattern Interrupt every 2-3 scenes by setting is_pattern_interrupt=True to force a sudden visual or audio shift."
        )
        user = f"Chosen Hook: {strategy.hook_concept}\nKey Facts: {research.key_statistics}\nDesign the structural beats."
        
        parsed = self.generate_structured(system, user, StoryBeatPlan)
        parsed.artifact_id = f"architect-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [strategy.artifact_id, research.artifact_id]
        return parsed


class ScriptWriterStage(BaseOpenAIStage):
    name = "script_writer"
    output_type = "StoryScript"
    
    def execute(self, inputs: Dict[str, Any]) -> StoryScript:
        beat_plan: StoryBeatPlan = inputs.get("story_beat_plan")
        research: ResearchPacket = inputs.get("research_packet")
        strategy: MarketingStrategy = inputs.get("marketing_strategy")
        global_feedback = inputs.get("global_feedback")
        
        if not beat_plan or not research:
            raise ValueError("Missing inputs for ScriptWriterStage")
            
        system = "You are a master scriptwriter. Write the exact narration for the provided structural beats. Ensure escalation and a cinematic tone. IMPORTANT: Keep the narration extremely punchy and fast-paced, suitable for a 60-second YouTube Short. The ENTIRE script must be under 150 words. The final output must exactly match the number of beats provided.\n\nCRITICAL RULE: The `narration` field MUST contain ONLY the exact words to be spoken by the voiceover artist. DO NOT include any stage directions, visual cues, speaker labels (like 'Narrator:'), or formatting notes. It will be sent directly to a Text-To-Speech engine."
        
        if global_feedback:
            learnings = "\n".join(global_feedback.get("pacing_learnings", []) if isinstance(global_feedback, dict) else global_feedback.pacing_learnings)
            system += f"\n\nHISTORICAL PERFORMANCE FEEDBACK (PACING):\n{learnings}\nApply this pacing feedback to your writing style."
        
        beat_text = "\n".join([f"[{b.beat_id}] Intent: {b.intent}" for b in beat_plan.beats])
        title = strategy.get("title_ideas", [""])[0] if isinstance(strategy, dict) else strategy.title_ideas[0]
        user = f"Title Idea: {title}\nResearch: {[f.claim for f in research.facts]}\nBeats:\n{beat_text}\nWrite the narration."
        
        parsed = self.generate_structured(system, user, StoryScript)
        
        parsed.total_word_count = sum(b.word_count for b in parsed.beats)
        parsed.artifact_id = f"story-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [beat_plan.artifact_id, research.artifact_id]
        return parsed


class RetentionCriticStage(BaseOpenAIStage):
    name = "retention_critic"
    output_type = "CriticReview"
    
    def execute(self, inputs: Dict[str, Any]) -> CriticReview:
        story: StoryScript = inputs.get("story_script")
        if not story:
            raise ValueError("Missing story_script")
            
        system = "You are a brutal YouTube retention critic. Read the script and explicitly identify weak points, low information density, or boring sections where viewers will click off. Do not rewrite, just critique."
        
        script_text = "\\n".join([f"[{b.beat_id}] {b.narration}" for b in story.beats])
        user = f"Critique this script for retention drops:\n\n{script_text}"
        
        parsed = self.generate_structured(system, user, CriticReview)
        parsed.artifact_id = f"critic-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [story.artifact_id]
        return parsed


class ScriptRewriterStage(BaseOpenAIStage):
    name = "script_rewriter"
    output_type = "EditedStoryScript"
    
    def execute(self, inputs: Dict[str, Any]) -> EditedStoryScript:
        story: StoryScript = inputs.get("story_script")
        critic: CriticReview = inputs.get("critic_review")
        
        if not story or not critic:
            raise ValueError("Missing inputs for ScriptRewriterStage")
            
        if critic.is_approved:
            # If already perfect, just cast it to EditedStoryScript
            logger.info("Critic approved script without changes.")
            return EditedStoryScript(
                artifact_id=f"edited-story-{self.video_id}",
                video_id=self.video_id,
                artifact_type="EditedStoryScript",
                parent_artifact_ids=[story.artifact_id, critic.artifact_id],
                title_variant=story.title_variant,
                beats=story.beats,
                total_word_count=story.total_word_count
            )
            
        system = "You are a master retention rewriter. Take the original script and the critic's harsh feedback, and rewrite only the problematic beats to dramatically improve retention. Return the complete updated script. IMPORTANT: Keep the entire script under 150 words for a fast-paced 60-second YouTube Short.\n\nCRITICAL RULE: The `narration` field MUST contain ONLY the exact words to be spoken by the voiceover artist. DO NOT include any stage directions, visual cues, camera movements, speaker labels, or notes (e.g. 'Investor turn:'). It will be sent directly to a Text-To-Speech engine."
        
        script_text = "\n".join([f"[{b.beat_id}] {b.narration}" for b in story.beats])
        
        if hasattr(critic, 'weak_points') and hasattr(critic, 'suggestions'):
            critic_feedback = "\n".join(critic.weak_points + critic.suggestions)
        elif hasattr(critic, 'critical_flaws'):
            critic_feedback = "\n".join(critic.critical_flaws)
        else:
            critic_feedback = str(critic)
        
        user = f"Original Script:\n{script_text}\n\nCritic Feedback:\n{critic_feedback}\n\nRewrite to fix all issues."
        
        parsed = self.generate_structured(system, user, EditedStoryScript)
        parsed.artifact_id = f"edited-story-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [story.artifact_id, critic.artifact_id]
        parsed.total_word_count = sum(b.word_count for b in parsed.beats)
        return parsed

class QualityEvaluatorStage(BaseOpenAIStage):
    name = "quality_evaluation"
    output_type = "QualityScoreReport"

    def execute(self, inputs: Dict[str, Any]) -> BaseModel:
        story = inputs.get("story_script")
        
        prompt = f"""
        You are an expert YouTube Retention Critic and Quality Assurance AI.
        Your job is to strictly evaluate the following YouTube documentary script before it is rendered.
        
        Evaluate it on two dimensions:
        1. Hook Score (1-10): Is the first 30 seconds grabbing attention and making a specific promise?
        2. Retention Score (1-10): Are there enough pattern interrupts? Is the pacing fast? Is there low information density?
        
        Then give an overall_score (1-10). If overall_score >= 7, set is_approved = True.
        Otherwise, set is_approved = False and list specific critical_flaws that must be rewritten.
        
        Script to evaluate:
        {story.model_dump_json() if hasattr(story, 'model_dump_json') else str(story)}
        """
        
        system_prompt = "You are an elite YouTube Video Quality Gate. Be extremely strict."
        parsed = self.generate_structured(system_prompt, prompt, QualityScoreReport)
        
        parsed.artifact_id = f"quality-{self.video_id}"
        parsed.video_id = self.video_id
        parsed.parent_artifact_ids = [story.artifact_id] if hasattr(story, 'artifact_id') else []
        return parsed
