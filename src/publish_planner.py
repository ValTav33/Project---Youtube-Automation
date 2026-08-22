import logging
import os
import time
import urllib.parse
import requests
from typing import Dict, Any

from pydantic import BaseModel, Field
from stage_runner import PipelineStage
from story_engines import BaseOpenAIStage
from contracts import MarketingStrategy, ThumbnailPromptPlan, EditedStoryScript, PublishPackage

logger = logging.getLogger(__name__)

class PublishMetadataPlan(BaseModel):
    description: str = Field(description="A comprehensive YouTube description including the hook and key insights")
    tags: list[str] = Field(description="10-15 highly relevant SEO tags for YouTube")

class PublishPackageStage(BaseOpenAIStage):
    """
    Generates YouTube metadata (Title, Description, Tags) and Thumbnail assets
    based on the original PromiseContract and the final StoryScript.
    """
    name = "publish_packaging"
    output_type = "PublishPackage"

    def execute(self, inputs: Dict[str, Any]) -> PublishPackage:
        strategy_raw = inputs.get("marketing_strategy")
        prompt_raw = inputs.get("thumbnail_prompt_plan")
        story_raw = inputs.get("story_script")
        
        if not strategy_raw or not prompt_raw or not story_raw:
            raise ValueError("Missing inputs")
            
        strategy = MarketingStrategy.model_validate(strategy_raw) if isinstance(strategy_raw, dict) else strategy_raw
        prompt_plan = ThumbnailPromptPlan.model_validate(prompt_raw) if isinstance(prompt_raw, dict) else prompt_raw
        story = EditedStoryScript.model_validate(story_raw) if isinstance(story_raw, dict) else story_raw

        # 1. Generate Metadata via LLM (Just Desc & Tags now, Title is from Strategy)
        title = strategy.title_ideas[0]
        
        prompt = (
            f"You are an expert YouTube strategist.\n"
            f"Review the final generated story script and the chosen title.\n"
            f"TITLE: {title}\n"
            f"Generate the perfect YouTube Description, and Tags to fulfill this promise.\n"
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
            logger.info(f"Generating thumbnail via GPT-Image-2 with Prompt:\n{prompt_plan.optimized_image_prompt}")
            try:
                openai_api_key = os.getenv("OPENAI_API_KEY")
                if not openai_api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment")
                    
                response = self.client.images.generate(
                    model="gpt-image-2",
                    prompt=prompt_plan.optimized_image_prompt + " (Must be a highly professional YouTube documentary thumbnail without any text or words).",
                    n=1,
                    size="1024x1024"
                )
                
                if response.data:
                    import base64
                    import requests
                    image_content = None
                    
                    if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
                        image_content = base64.b64decode(response.data[0].b64_json)
                    elif hasattr(response.data[0], 'url') and response.data[0].url:
                        image_url = response.data[0].url
                        image_resp = requests.get(image_url, timeout=25)
                        if image_resp.status_code == 200 and len(image_resp.content) > 1000:
                            image_content = image_resp.content
                        else:
                            logger.error(f"[{self.name}] Failed to download OpenAI image from URL: {image_url}")
                    
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
                        logger.error(f"[{self.name}] OpenAI API Error: No valid image data returned")
                else:
                    logger.error(f"[{self.name}] OpenAI API Error: No data returned")
            except Exception as e:
                logger.error(f"[{self.name}] Thumbnail generation error: {e}")
                
            if not thumbnail_urls:
                # Ultimate fallback
                thumbnail_urls = ["https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1280&q=80"]

        # 3. Assemble Publish Package
        return PublishPackage(
            artifact_id=f"publish-{self.video_id}",
            video_id=self.video_id,
            parent_artifact_ids=[story.artifact_id, strategy.artifact_id, prompt_plan.artifact_id],
            title=title,
            description=metadata_plan.description,
            tags=metadata_plan.tags,
            thumbnail_urls=thumbnail_urls,
            privacy_status="private" # Default to private for review
        )
