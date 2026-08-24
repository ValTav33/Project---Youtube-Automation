import pytest
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from orchestrator_v3 import V3Orchestrator
from agents_v3 import MockQAAgent
from contracts_v3 import ProductionManifest

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OPENAI_API_KEY")
def test_v3_repair_loop():
    """
    Tests the QA and Repair loop. We run the generation phase,
    then use the MockQAAgent to create an EditorRepairPlan,
    and then run the repair phase to verify the manifest is updated.
    """
    orchestrator = V3Orchestrator(db_client=None)
    
    video_id = "test-repair-video-1"
    topic = "The Future of AI Coding"
    
    # 1. Generation
    manifest = orchestrator.process_generation_phase(video_id, topic)
    assert manifest is not None
    assert manifest.revision == 1
    
    # Find the original asset URL (if any)
    original_asset = None
    for shot in manifest.shots:
        if shot.asset_url:
            original_asset = shot.asset_url
            break
            
    assert original_asset is not None, "Pipeline must generate at least one shot with an asset"
    
    # We need access to the intermediate artifacts to run repair
    # In a real system, we'd fetch them from the DB using video_id.
    # Since orchestrator_v3.py doesn't return them currently, we'll manually re-instantiate them just for this test
    from agents_v3 import StrategyAgent, MockResearchAgent, StoryAgent, VisualDirectorAgent, MockAudioDirectorAgent
    strategy_agent = StrategyAgent()
    brief = strategy_agent.generate_brief(video_id, topic)
    research_agent = MockResearchAgent()
    research = research_agent.run_research(video_id, brief)
    story_agent = StoryAgent()
    story = story_agent.draft_story(video_id, brief, research)
    visual_agent = VisualDirectorAgent()
    visuals = visual_agent.assign_visuals(video_id, story)
    audio_agent = MockAudioDirectorAgent()
    audio = audio_agent.plan_audio(video_id, story, visuals)
    
    # 2. QA
    qa_agent = MockQAAgent()
    repair_plan = qa_agent.run_qa(video_id, manifest, visuals)
    assert len(repair_plan.repairs) > 0
    assert repair_plan.repairs[0].issue_type == "asset_replacement"
    
    # 3. Repair
    repaired_manifest = orchestrator.process_repair_phase(video_id, repair_plan, story, visuals, audio)
    
    assert repaired_manifest is not None
    assert repaired_manifest.revision == 2
    
    # Verify the asset actually changed
    new_asset = None
    for shot in repaired_manifest.shots:
        if shot.asset_url:
            new_asset = shot.asset_url
            break
            
    assert new_asset is not None
    assert new_asset != original_asset
    assert "Unsplash (Repaired)" in [s.provenance["provider"] for s in repaired_manifest.shots if s.provenance]
    
    print("\nRepair Loop Success!")
