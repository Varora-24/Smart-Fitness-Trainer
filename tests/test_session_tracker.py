# ================================================================
#  tests/test_session_tracker.py  –  Session tracker unit tests
# ================================================================

from core.data.session_tracker import WorkoutSession

# ── Test 1.8 & 1.11: Retain multiple exercises in CSV export ──────
def test_session_accumulates_and_exports_all_exercises(tmp_path, monkeypatch):
    # Redirect DATASET_CSV_PATH to an isolated temp file for this test only,
    # so the test never touches the real rep_dataset.csv at the repo root.
    fake_csv = tmp_path / "rep_dataset_test.csv"
    monkeypatch.setattr("core.data.session_tracker.DATASET_CSV_PATH", str(fake_csv))

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
    assert fake_csv.exists()
    
    with open(fake_csv, "r") as fh:
        lines = fh.readlines()
        
    # Header + 2 data rows
    assert len(lines) >= 3
    # Check that both exercises are represented
    content = "".join(lines)
    assert "squats" in content
    assert "curls" in content
