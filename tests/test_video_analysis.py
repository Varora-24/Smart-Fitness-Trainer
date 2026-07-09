# ================================================================
#  tests/test_video_analysis.py  –  Video analysis pipeline tests
# ================================================================
#  Feeds synthetic frames through FramePipeline (same code path as
#  the Video Analysis page) and verifies the summary structure.
#  No real video file needed — mocks cv2.VideoCapture like
#  test_webcam_retry.py already does.
# ================================================================

import numpy as np
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def blank_frames():
    """Generate a list of 10 blank 720p frames."""
    return [np.zeros((720, 1280, 3), dtype=np.uint8) for _ in range(10)]


class TestVideoAnalysisPipeline:
    """Tests that FramePipeline correctly processes a batch of frames."""

    def test_pipeline_returns_summary_with_expected_keys(self, blank_frames):
        """Process synthetic frames and check the summary dict structure."""
        from frame_pipeline import FramePipeline

        pipeline = FramePipeline(exercise_key="squats", in_setup=False)
        pipeline.voice_muted = True

        for frame in blank_frames:
            result = pipeline.process_frame(frame)
            # Should return an image (numpy array) of the same shape
            assert isinstance(result, np.ndarray)
            assert result.shape[0] > 0 and result.shape[1] > 0

        summary = pipeline.get_summary()
        assert isinstance(summary, dict)

        # Verify all expected keys are present
        expected_keys = [
            "total_reps", "clean_reps", "bad_reps",
            "calories", "duration_secs", "reps_per_min",
            "avg_rep_score", "avg_symmetry", "avg_form",
        ]
        for key in expected_keys:
            assert key in summary, f"Missing key: {key}"

    def test_pipeline_processes_multiple_exercises(self, blank_frames):
        """Switching exercises mid-video doesn't crash."""
        from frame_pipeline import FramePipeline

        pipeline = FramePipeline(exercise_key="squats", in_setup=False)
        pipeline.voice_muted = True

        # Process first 5 as squats
        for frame in blank_frames[:5]:
            pipeline.process_frame(frame)

        # Switch to curls
        pipeline.set_exercise("curls")
        for frame in blank_frames[5:]:
            pipeline.process_frame(frame)

        summary = pipeline.get_summary()
        assert isinstance(summary, dict)
        assert "total_reps" in summary

    def test_mock_video_capture_flow(self, blank_frames):
        """Simulate the exact flow from the Video Analysis page using a mock VideoCapture."""
        from frame_pipeline import FramePipeline

        mock_cap = MagicMock()
        # Return True + frame for each blank frame, then False to stop
        side_effects = [(True, f) for f in blank_frames] + [(False, None)]
        mock_cap.read.side_effect = side_effects
        mock_cap.get.return_value = 30.0  # FPS
        mock_cap.isOpened.return_value = True

        pipeline = FramePipeline(exercise_key="pushups", in_setup=False)
        pipeline.voice_muted = True

        output_frames = []
        while True:
            success, frame = mock_cap.read()
            if not success:
                break
            annotated = pipeline.process_frame(frame)
            output_frames.append(annotated)

        assert len(output_frames) == len(blank_frames)
        summary = pipeline.get_summary()
        assert summary["total_reps"] >= 0  # no crash, valid result
