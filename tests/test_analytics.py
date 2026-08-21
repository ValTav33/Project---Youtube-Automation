import unittest
from unittest.mock import MagicMock, patch
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from contracts import PromiseContract, EditedStoryScript, ShotPlan, PublishPackage, AnalyticsFeatureVector
from analytics_extractor import AnalyticsFeatureVectorStage

class TestAnalyticsExtractor(unittest.TestCase):
    def test_analytics_extraction(self):
        sb = MagicMock()
        stage = AnalyticsFeatureVectorStage(sb, "test_video")

        promise = PromiseContract(
            artifact_type="PromiseContract",
            artifact_id="promise-1",
            video_id="test_video",
            target_title="Test",
            topic_premise="Premise",
            primary_claim="Claim",
            target_emotion="Emotion",
            hook_promise="Hook",
            narrative_arc="Arc"
        )

        story = EditedStoryScript(
            artifact_type="EditedStoryScript",
            artifact_id="story-1",
            video_id="test_video",
            title_variant="Title",
            beats=[],
            total_word_count=0
        )

        from contracts import Shot
        shot_obj = Shot(shot_id="s1", scene_id="s", description="d", duration_seconds=1.0, start_frame=0, end_frame=30, duration_frames=30)
        
        shots = ShotPlan(
            artifact_type="ShotPlan",
            artifact_id="shot-1",
            video_id="test_video",
            shots=[shot_obj, shot_obj, shot_obj] # 3 shots
        )

        publish = PublishPackage(
            artifact_type="PublishPackage",
            artifact_id="pub-1",
            video_id="test_video",
            title="Final Title",
            description="Desc",
            tags=["a"],
            thumbnail_concept="Thumb",
            thumbnail_urls=[],
            privacy_status="unlisted"
        )

        # Mock the LLM call
        mock_feature_vector = AnalyticsFeatureVector(
            artifact_type="AnalyticsFeatureVector",
            artifact_id="av-1",
            video_id="test_video",
            topic_category="Tech",
            hook_type="Curiosity",
            hook_duration_seconds=15.0,
            total_shots=0, # Overwritten by extractor
            first_minute_shot_count=0, # Overwritten
            open_loop_count=1,
            music_profile="Dramatic",
            title_strategy="Direct",
            thumbnail_strategy="Face",
            style_profile_version="v2_standard"
        )

        stage.generate_structured = MagicMock(return_value=mock_feature_vector)

        result = stage.execute({
            "promise_contract": promise,
            "story_script": story,
            "shot_plan": shots,
            "publish_package": publish
        })

        self.assertEqual(result.topic_category, "Tech")
        self.assertEqual(result.total_shots, 3)
        self.assertEqual(result.first_minute_shot_count, 3)

class TestAnalyticsIngestion(unittest.TestCase):
    @patch('analytics_ingestion.get_authenticated_service')
    @patch('analytics_ingestion.create_client')
    def test_ingestion(self, mock_create_client, mock_auth):
        from analytics_ingestion import ingest_analytics
        
        # Mock Supabase
        mock_sb = MagicMock()
        mock_create_client.return_value = mock_sb
        
        # Mock videos in DB
        mock_res = MagicMock()
        mock_res.data = [{"id": "vid_1", "youtube_video_id": "yt_1"}]
        mock_sb.table().select().not_is().execute.return_value = mock_res
        
        # Mock YouTube Data API
        mock_yt = MagicMock()
        mock_auth.return_value = mock_yt
        
        mock_yt.videos().list().execute.return_value = {
            "items": [
                {
                    "statistics": {
                        "viewCount": "100",
                        "likeCount": "10",
                        "commentCount": "5"
                    }
                }
            ]
        }
        
        # We need an env var for the test to bypass credential checks
        with patch.dict(os.environ, {"SUPABASE_URL": "test", "SUPABASE_SERVICE_ROLE_KEY": "test"}):
            ingest_analytics()
            
        # Verify it inserted into analytics
        mock_sb.table.assert_any_call("youtube_analytics_snapshots")
        mock_sb.table().insert.assert_called_once()
        args, kwargs = mock_sb.table().insert.call_args
        
        self.assertEqual(args[0]["views"], 100)
        self.assertEqual(args[0]["likes"], 10)

if __name__ == '__main__':
    unittest.main()
