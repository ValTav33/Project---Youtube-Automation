import pytest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from orchestrator_v3 import V3Orchestrator
from contracts_v3 import ProductionManifest
import logging

logging.basicConfig(level=logging.INFO)

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
def test_v3_end_to_end_pipeline():
    """
    Tests the full execution of the V3 AI pipeline from topic to final manifest.
    This will actually call OpenAI.
    """
    orchestrator = V3Orchestrator(db_client=None)
    
    # Needs to start in discovered or approved
    video_id = "test-e2e-video-1"
    topic = "The Economics of AI Automation"
    
    # We pretend it was in 'approved' state
    manifest = orchestrator.process_generation_phase(video_id, topic)
    
    # Assertions
    assert manifest is not None
    assert isinstance(manifest, ProductionManifest)
    assert manifest.video_id == video_id
    assert manifest.total_frames > 0
    assert len(manifest.shots) > 0
    
    # Verify the structure matches exactly what Remotion needs
    manifest_dict = manifest.model_dump()
    assert "shots" in manifest_dict
    assert "component_type" in manifest_dict["shots"][0]
    
    # Optionally save it for the gallery test
    out_path = os.path.join(os.getcwd(), "remotion", "src", "fixtures", "e2e_output.json")
    with open(out_path, "w") as f:
        f.write(manifest.model_dump_json(indent=2))
        
    print(f"\nEnd-to-End Pipeline Success! Wrote fixture to {out_path}")

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
def test_v3_long_form_pipeline():
    """
    Tests the scaling of the V3 AI pipeline for a 10-minute video.
    Mocks ElevenLabs, Pexels, and DALL-E to avoid excessive API costs, 
    but tests the StoryAgent word count pacing and ManifestCompiler duration logic.
    """
    os.environ["MOCK_EXTERNAL_APIS"] = "true"
    
    orchestrator = V3Orchestrator(db_client=None)
    video_id = "test-longform-1"
    topic = "The Rise of Autonomous AI Agents"
    
    # Process with StrategyAgent requesting 10 minutes (600s)
    # The default test in orchestrator uses generate_brief with 600s now
    manifest = orchestrator.process_generation_phase(video_id, topic)
    
    assert manifest is not None
    assert manifest.total_frames > 6000 # At least 6000 frames for a long video (30fps * 200s minimum)
    
    os.environ["MOCK_EXTERNAL_APIS"] = "false"
    print(f"\nLong-Form Pipeline Success! Total frames: {manifest.total_frames}")
