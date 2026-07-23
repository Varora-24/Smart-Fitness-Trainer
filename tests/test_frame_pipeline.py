# ================================================================
#  tests/test_frame_pipeline.py  –  FramePipeline unit tests
# ================================================================

from unittest.mock import patch
from core.tracking.frame_pipeline import FramePipeline

@patch("core.tracking.frame_pipeline.PoseDetector")
def test_pipeline_set_exercise_resets_tracker(mock_detector_cls):
    pipeline = FramePipeline(exercise_key="squats", in_setup=False)
    assert pipeline.current_key == "squats"
    assert pipeline.tracker.key == "squats"

    # Simulate some changes in tracker state
    pipeline.tracker.total_reps = 3
    
    # Switch exercise
    pipeline.set_exercise("curls")
    assert pipeline.current_key == "curls"
    assert pipeline.tracker.key == "curls"
    # Verify tracker is reset and total_reps is 0
    assert pipeline.tracker.total_reps == 0
    assert pipeline.prev_rep_count == 0
    assert pipeline.flash_frames == 0

@patch("core.tracking.frame_pipeline.PoseDetector")
def test_pipeline_get_summary_keys(mock_detector_cls):
    pipeline = FramePipeline(exercise_key="squats", in_setup=False)
    summary = pipeline.get_summary()
    
    # Verify expected keys are present
    expected_keys = {
        "total_reps", "clean_reps", "bad_reps", "calories",
        "duration_secs", "reps_per_min", "avg_rep_score",
        "avg_symmetry", "avg_form"
    }
    assert expected_keys.issubset(summary.keys())

@patch("core.tracking.frame_pipeline.PoseDetector")
def test_pipeline_rep_label_thresholding(mock_detector_cls):
    pipeline = FramePipeline(exercise_key="squats", in_setup=False)
    pipeline.ml_model = None  # Force blended score to equal rule score
    
    # Mock PoseDetector results and position list to pass gates
    pipeline.detector.find_position.return_value = [[i, 50, 100] for i in range(33)]  # type: ignore  # type: ignore
    pipeline.detector.find_pose = lambda img, *args, **kwargs: img  # type: ignore  # type: ignore
    
    # We mock tracker.update to simulate a rep finishing with a score of 63.0
    # 63.0 is below clean_depth (70) for squats, but above CLEAN_REP_SCORE_THRESHOLD (60.0)
    def mock_update(*args, **kwargs):
        pipeline.tracker.total_reps = 1
        pipeline.tracker.rep_score = 63.0
        pipeline.tracker._feature_rows = [{
            "exercise": "squats",
            "symmetry": 90.0,
            "range_of_motion": 90.0,
            "posture": 90.0,
            "control": 90.0,
        }]
    pipeline.tracker.update = mock_update  # type: ignore  # type: ignore
    
    import numpy as np
    dummy_img = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Execute frame processing
    pipeline.process_frame(dummy_img)
    
    # Check that rep was recorded
    assert pipeline.prev_rep_count == 1
    assert len(pipeline.session._all_feature_rows) == 1
    
    # Verify label is good_rep despite 63 < clean_depth (70)
    saved_row = pipeline.session._all_feature_rows[0]
    assert saved_row["rep_score"] == 63.0
    assert saved_row["rep_label"] == "good_rep"
