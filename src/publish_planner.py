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
        promise_raw = inputs.get("promise_contract")
        story_raw = inputs.get("story_script")
        
        if not promise_raw or not story_raw:
            raise ValueError("Missing inputs")
            
        promise = PromiseContract.model_validate(promise_raw) if isinstance(promise_raw, dict) else promise_raw
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw

        # Handle both dict (from DB cache) and Pydantic objects
        topic_premise = promise.topic_premise
        primary_claim = promise.primary_claim
        target_emotion = promise.target_emotion

        # 1. Generate Metadata via LLM
        prompt = (
            f"You are an expert YouTube strategist.\n"
            f"Review the original promise and the final generated story script.\n"
            f"PROMISE: {topic_premise}\n"
            f"CLAIM: {primary_claim}\n"
            f"EMOTION: {target_emotion}\n\n"
            f"Generate the perfect YouTube Title, Description, and Tags to fulfill this promise.\n"
            f"Also, write a highly descriptive 'thumbnail_concept' prompt (max 3 sentences) "
            f"optimized for DALL-E 3. The thumbnail should be professional, highly cinematic, "
            f"feature extreme contrast, have a central focal point, and contain NO text or logos. "
            f"Make it look like a high-budget documentary cover."
        )

        metadata_plan = self.generate_structured(
            system_prompt="You are a YouTube metadata optimizer.",
            user_prompt=prompt,
            response_format=PublishMetadataPlan
        )

        # 2. Generate Thumbnails (via DALL-E 3 or Mock)
        thumbnail_urls = []
        is_mock = os.getenv("MOCK_EXTERNAL_APIS", "false").lower() == "true"

        if is_mock:
            logger.info(f"[{self.name}] MOCK MODE: Returning placeholder thumbnails.")
            thumbnail_urls = [
                "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1280&q=80"
            ]
        else:
            logger.info(f"[{self.name}] Generating thumbnail via DALL-E 3 for concept: {metadata_plan.thumbnail_concept}")
            try:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")
                    
                payload = {
                    "model": "gpt-image-2",
                    "prompt": metadata_plan.thumbnail_concept + " (Must be a highly professional YouTube documentary thumbnail without any text or words).",
                    "n": 1,
                    "size": "1792x1024"
                }
                headers = {
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                resp = requests.post("https://api.openai.com/v1/images/generations", json=payload, headers=headers, timeout=45)
                if resp.status_code == 200:
                    data_obj = resp.json()["data"][0]
                    
                    image_content = None
                    if "url" in data_obj:
                        image_url = data_obj["url"]
                        image_resp = requests.get(image_url, timeout=25)
                        if image_resp.status_code == 200 and len(image_resp.content) > 1000:
                            image_content = image_resp.content
                        else:
                            logger.error(f"[{self.name}] Failed to download OpenAI image from URL.")
                    elif "b64_json" in data_obj:
                        import base64
                        image_content = base64.b64decode(data_obj["b64_json"])
                    
                    if image_content:
                        storage_filename = f"thumb_{self.video_id}_{int(time.time())}_gptimage.jpg"
                        self.sb.storage.from_("thumbnails").upload(
                            path=storage_filename,
                            file=image_content,
                            file_options={"content-type": "image/jpeg", "upsert": "true"}
                        )
                        public_url = self.sb.storage.from_("thumbnails").get_public_url(storage_filename)
                        
                        actual_url = public_url if isinstance(public_url, str) else public_url.get("publicUrl", "")
                        thumbnail_urls.append(actual_url)
                        logger.info(f"[{self.name}] ✅ GPT Image Thumbnail saved to Supabase: {actual_url}")
                    else:
                        logger.error(f"[{self.name}] Failed to extract valid image from OpenAI response.")
                else:
                    logger.error(f"[{self.name}] OpenAI API Error: {resp.status_code} {resp.text}")
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
