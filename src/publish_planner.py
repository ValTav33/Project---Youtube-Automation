import logging
import os
import time
import urllib.parse
import requests
from typing import Dict, Any

from pydantic import BaseModel, Field
from stage_runner import PipelineStage
from story_engines import BaseOpenAIStage
from contracts import PromiseContract, EditedStoryScript, PublishPackage

logger = logging.getLogger(__name__)

class PublishMetadataPlan(BaseModel):
    title: str = Field(description="A highly engaging, high-CTR YouTube title (max 60 characters recommended)")
    description: str = Field(description="A comprehensive YouTube description including the hook and key insights")
    tags: list[str] = Field(description="10-15 highly relevant SEO tags for YouTube")
    thumbnail_concept: str = Field(description="A visual description for an AI image generator to create the thumbnail")

class PublishPackageStage(BaseOpenAIStage):
    """
    Generates YouTube metadata (Title, Description, Tags) and Thumbnail assets
    based on the original PromiseContract and the final StoryScript.
    """
    name = "publish_packaging"
    output_type = "PublishPackage"

    def execute(self, inputs: Dict[str, Any]) -> PublishPackage:
        promise: PromiseContract = inputs.get("promise_contract")
        story: EditedStoryScript = inputs.get("story_script")

        if not promise or not story:
            raise ValueError("Missing promise_contract or story_script for PublishPackageStage")

        # 1. Generate Metadata via LLM
        prompt = (
            f"You are an expert YouTube strategist.\n"
            f"Review the original promise and the final generated story script.\n"
            f"PROMISE: {promise.topic_premise}\n"
            f"CLAIM: {promise.primary_claim}\n"
            f"EMOTION: {promise.target_emotion}\n\n"
            f"Generate the perfect YouTube Title, Description, and Tags to fulfill this promise.\n"
            f"Also, write a highly descriptive 'thumbnail_concept' prompt (max 2 sentences) "
            f"for an image generator. The thumbnail should be dramatic, cinematic, and minimalist."
        )

        metadata_plan = self._generate_structured(
            system_prompt="You are a YouTube metadata optimizer.",
            user_prompt=prompt,
            response_model=PublishMetadataPlan
        )

        # 2. Generate Thumbnails (via Pollinations API or Mock)
        thumbnail_urls = []
        is_mock = os.getenv("MOCK_EXTERNAL_APIS", "false").lower() == "true"

        if is_mock:
            logger.info(f"[{self.name}] MOCK MODE: Returning placeholder thumbnails.")
            thumbnail_urls = [
                "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1280&q=80"
            ]
        else:
            logger.info(f"[{self.name}] Generating thumbnails via Pollinations Flux for concept: {metadata_plan.thumbnail_concept}")
            for i in range(2):
                try:
                    encoded_prompt = urllib.parse.quote(f"{metadata_plan.thumbnail_concept}, variant {i+1}")
                    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&model=flux&seed={i * 42 + 7}"
                    
                    resp = requests.get(pollinations_url, timeout=25)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        storage_filename = f"thumb_{self.video_id}_{int(time.time())}_{i+1}.jpg"
                        self.sb.storage.from_("thumbnails").upload(
                            path=storage_filename,
                            file=resp.content,
                            file_options={"content-type": "image/jpeg", "upsert": "true"}
                        )
                        public_url = self.sb.storage.from_("thumbnails").get_public_url(storage_filename)
                        thumbnail_urls.append(public_url)
                        logger.info(f"[{self.name}] ✅ Thumbnail #{i+1} saved to Supabase: {public_url}")
                    else:
                        thumbnail_urls.append(pollinations_url)
                except Exception as e:
                    logger.error(f"[{self.name}] Thumbnail generation error: {e}")
                    
            if not thumbnail_urls:
                # Ultimate fallback
                thumbnail_urls = ["https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1280&q=80"]

        # 3. Assemble Publish Package
        return PublishPackage(
            artifact_id=f"pub_{self.video_id}_{int(time.time())}",
            video_id=self.video_id,
            title=metadata_plan.title,
            description=metadata_plan.description,
            tags=metadata_plan.tags,
            thumbnail_urls=thumbnail_urls,
            privacy_status="private" # Default to private for review
        )
