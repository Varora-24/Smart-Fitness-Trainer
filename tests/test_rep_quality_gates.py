# ================================================================
#  tests/test_rep_quality_gates.py  –  Verification of Rep Quality Gates
# ================================================================
import time
import pytest
from unittest.mock import MagicMock
from core.tracking.exercises import ExerciseTracker


class MockDetector:
    def __init__(self, visible=True):
        self.results = MagicMock()
        if visible:
            self.results.pose_landmarks = MagicMock()
            self.results.pose_landmarks.landmark = [
                MagicMock(visibility=1.0) for _ in range(33)
            ]
        else:
            self.results.pose_landmarks = None

    def find_angle(self, img, p1, p2, p3, draw=True):
        return 120.0

    def find_position(self, img, draw=False):
        return [[i, 50, 100] for i in range(33)]


def feed_frames(tracker, detector, img, lm_list, angle, posture, num_frames=8):
    """Feed identical frames to allow angle smoothing to converge."""
    for _ in range(num_frames):
        detector.find_angle = MagicMock(side_effect=[angle, angle, posture, posture]) # type: ignore # type: ignore
        tracker.update(detector, img, lm_list, draw=False)


@pytest.mark.parametrize("exercise_key,clean_angles,bad_angles,posture_base,bad_posture_delta", [
    ("curls", (160.0, 65.0), (155.0, 88.0), 10.0, 25.0), # Curls: clean ROM 95 deg (to 65 deg), bad ROM bounce near 90 (to 88 deg)
    ("squats", (165.0, 95.0), (155.0, 118.0), 170.0, 30.0), # Squats: clean ROM 70 deg (to 95 deg), bad shallow dip (to 118 deg)
    ("pushups", (160.0, 80.0), (158.0, 98.0), 175.0, 25.0), # Pushups: clean descent to 80 deg, bad dip to 98 deg
    ("shoulder_press", (90.0, 165.0), (95.0, 146.0), 160.0, 25.0), # Shoulder press (extension direction to 165 deg, bad dip to 146 deg)
])
def test_rep_quality_gates_telemetry(exercise_key, clean_angles, bad_angles, posture_base, bad_posture_delta, capsys):
    """
    Verify that deliberately clean repetitions score high without dilution,
    and deliberately bad (fast, shallow, or swinging) repetitions drop below 50.
    Prints actual recorded telemetry for engineering review.
    """
    print(f"\n=======================================================")
    print(f"TELEMETRY REPORT FOR: {exercise_key.upper()}")
    print(f"=======================================================")

    img = MagicMock()
    lm_list = [[i, 50, 100] for i in range(33)]

    # ─────────────────────────────────────────────────────────────
    # TEST CASE 1: Deliberately Clean, Controlled Rep
    # ─────────────────────────────────────────────────────────────
    tracker_clean = ExerciseTracker(exercise_key)
    detector_clean = MockDetector()
    is_up_direction = tracker_clean.cfg.get("depth_direction", "down") == "up"

    # Simulate start position (multiple frames for smoother convergence)
    start_angle, target_angle = clean_angles
    feed_frames(tracker_clean, detector_clean, img, lm_list, start_angle, posture_base, num_frames=8)

    # Simulate cadence & duration (backdate rep_start_time)
    min_dur = tracker_clean.cfg.get("min_duration_secs", 1.0)
    tracker_clean._rep_start_time = time.time() - (min_dur + 0.5)  # fully controlled tempo

    # Simulate moving through target depth/extension (multiple frames for convergence)
    feed_frames(tracker_clean, detector_clean, img, lm_list, target_angle, posture_base + 2.0, num_frames=8)

    # Simulate return to completion boundary
    tracker_clean.last_rep_time = 0.0  # avoid 0.3s debounce in synthetic loop
    feed_frames(tracker_clean, detector_clean, img, lm_list, start_angle, posture_base, num_frames=8)

    extreme_angle = tracker_clean.last_rep_max_angle if is_up_direction else tracker_clean.last_rep_min_angle
    op_str = ">=" if is_up_direction else "<="

    print(f"--> [CLEAN REP TEST]:")
    print(f"    Duration        : {tracker_clean.last_rep_duration:.2f}s (Min Req: >= {tracker_clean.cfg.get('min_duration_secs'):.1f}s)")
    print(f"    ROM Travel Span : {tracker_clean.last_rep_travel_deg:.1f} deg (Min Req: >= {tracker_clean.cfg.get('min_rom_travel_deg'):.1f} deg)")
    print(f"    Extreme Angle   : {extreme_angle:.1f} deg (Target: {op_str} {tracker_clean.cfg.get('rom_min_angle'):.1f} deg)")
    print(f"    Max Stability Delta : {tracker_clean.last_rep_posture_delta:.1f} deg (Max Tol: <= {tracker_clean.cfg.get('max_posture_deviation_deg'):.1f} deg)")
    print(f"    Failed Gates    : {tracker_clean.last_rep_failed_gates}")
    print(f"    Resulting Score : {tracker_clean.rep_score:.1f} / 100")
    print(f"    Classification  : {'CLEAN REP' if tracker_clean.last_rep_was_clean else 'BAD REP'}\n")

    assert tracker_clean.total_reps == 1, f"Clean rep must increment total_reps, got {tracker_clean.total_reps}"
    assert tracker_clean.clean_reps == 1, f"Clean rep must increment clean_reps, got {tracker_clean.clean_reps}. Failed gates: {tracker_clean.last_rep_failed_gates}"
    assert tracker_clean.last_rep_gates_passed is True, f"All gates must pass for clean rep. Failed: {tracker_clean.last_rep_failed_gates}"
    assert tracker_clean.rep_score >= 70.0, f"Clean rep score ({tracker_clean.rep_score}) must remain unpenalized in high band (>=70)"

    # ─────────────────────────────────────────────────────────────
    # TEST CASE 2: Deliberately Bad Rep (Fast, Shallow, Swinging)
    # ─────────────────────────────────────────────────────────────
    tracker_bad = ExerciseTracker(exercise_key)
    detector_bad = MockDetector()

    # Simulate start position
    bad_start, bad_target = bad_angles
    feed_frames(tracker_bad, detector_bad, img, lm_list, bad_start, posture_base, num_frames=8)

    # Simulate fast jerk / bounce (only 0.35 seconds duration)
    tracker_bad._rep_start_time = time.time() - 0.35

    # Simulate moving only to shallow boundary with severe body swing / compensation
    feed_frames(tracker_bad, detector_bad, img, lm_list, bad_target, posture_base + bad_posture_delta, num_frames=8)

    # Simulate immediate fast bounce back
    tracker_bad.last_rep_time = 0.0  # avoid 0.3s debounce in synthetic loop
    feed_frames(tracker_bad, detector_bad, img, lm_list, bad_start, posture_base + bad_posture_delta, num_frames=8)

    bad_extreme = tracker_bad.last_rep_max_angle if is_up_direction else tracker_bad.last_rep_min_angle

    print(f"--> [BAD REP TEST (Fast/Shallow/Swinging)]:")
    print(f"    Duration        : {tracker_bad.last_rep_duration:.2f}s (Min Req: >= {tracker_bad.cfg.get('min_duration_secs'):.1f}s)")
    print(f"    ROM Travel Span : {tracker_bad.last_rep_travel_deg:.1f} deg (Min Req: >= {tracker_bad.cfg.get('min_rom_travel_deg'):.1f} deg)")
    print(f"    Extreme Angle   : {bad_extreme:.1f} deg (Target: {op_str} {tracker_bad.cfg.get('rom_min_angle'):.1f} deg)")
    print(f"    Max Stability Delta : {tracker_bad.last_rep_posture_delta:.1f} deg (Max Tol: <= {tracker_bad.cfg.get('max_posture_deviation_deg'):.1f} deg)")
    print(f"    Failed Gates    : {tracker_bad.last_rep_failed_gates}")
    print(f"    Resulting Score : {tracker_bad.rep_score:.1f} / 100")
    print(f"    Classification  : {'CLEAN REP' if tracker_bad.last_rep_was_clean else 'BAD REP'}\n")

    assert tracker_bad.total_reps == 1, "Bad rep must STILL increment total_reps (reps must never be dropped)"
    assert tracker_bad.bad_reps == 1, "Bad rep must increment bad_reps count"
    assert tracker_bad.last_rep_gates_passed is False, "Bad rep must fail at least one quality gate"
    assert tracker_bad.rep_score < 50.0, f"Bad rep score ({tracker_bad.rep_score}) must be strictly capped below 50.0!"
