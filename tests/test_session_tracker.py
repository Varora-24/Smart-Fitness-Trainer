# ================================================================
#  tests/test_session_tracker.py  –  Session tracker unit tests
# ================================================================

import os
from session_tracker import WorkoutSession
from config import DATASET_CSV_PATH

# ── Test 1.8 & 1.11: Retain multiple exercises in CSV export ──────
def test_session_accumulates_and_exports_all_exercises():
    # Remove existing dataset if present to avoid interference
    if os.path.exists(DATASET_CSV_PATH):
        try:
            os.remove(DATASET_CSV_PATH)
        except Exception:
            pass

    session = WorkoutSession()
    
    # Simulate adding feature rows for squats
    row1 = {
        "exercise": "squats", "symmetry": 90.0, "range_of_motion": 95.0,
        "posture": 100.0, "control": 92.0, "rep_score": 94.0, "rep_label": "good_rep"
    }
    session.add_feature_row(row1)
    
    # Simulate adding feature rows for curls (switching exercise)
    row2 = {
        "exercise": "curls", "symmetry": 85.0, "range_of_motion": 88.0,
        "posture": 100.0, "control": 95.0, "rep_score": 91.0, "rep_label": "good_rep"
    }
    session.add_feature_row(row2)
    
    # Export
    session.export_csv()
    
    # Verify CSV file is created and contains correct data
    assert os.path.exists(DATASET_CSV_PATH)
    
    with open(DATASET_CSV_PATH, "r") as fh:
        lines = fh.readlines()
        
    # Header + 2 data rows
    assert len(lines) >= 3
    # Check that both exercises are represented
    content = "".join(lines)
    assert "squats" in content
    assert "curls" in content
    
    # Clean up
    if os.path.exists(DATASET_CSV_PATH):
        try:
            os.remove(DATASET_CSV_PATH)
        except Exception:
            pass
