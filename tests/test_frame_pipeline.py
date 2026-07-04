# ================================================================
#  tests/test_frame_pipeline.py  –  FramePipeline unit tests
# ================================================================

from frame_pipeline import FramePipeline

def test_pipeline_set_exercise_resets_tracker():
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

def test_pipeline_get_summary_keys():
    pipeline = FramePipeline(exercise_key="squats", in_setup=False)
    summary = pipeline.get_summary()
    
    # Verify expected keys are present
    expected_keys = {
        "total_reps", "clean_reps", "bad_reps", "calories",
        "duration_secs", "reps_per_min", "avg_rep_score",
        "avg_symmetry", "avg_form"
    }
    assert expected_keys.issubset(summary.keys())
