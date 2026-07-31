# ================================================================
#  tests/test_yoga_tracker.py  -  Unit tests for YogaPoseTracker
# ================================================================
#
#  Mirrors the mocked-detector pattern from test_exercises.py.
#  Uses synthetic lm_list values to drive the yoga tracker without
#  needing a real camera or MediaPipe model.
#
#  Coverage:
#   1. Correct pose held for full duration registers as completed.
#   2. Pose broken before min duration does NOT register as completed.
#   3. Alignment score responds correctly to landmark deviation.
#   4. Hold timer resets when alignment drops below threshold.
#   5. Unknown pose key raises ValueError.
#   6. Missing landmarks give alignment_score=0 and no hold.
#   7. reset_completion() re-enables completion detection.
# ================================================================

import time
from unittest.mock import MagicMock

import numpy as np
import pytest

from core.tracking.yoga_tracker import YogaPoseTracker, _compute_angle


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_lm_list(positions: dict, n: int = 33) -> list:
    """
    Build a synthetic lm_list in the format [id, x_px, y_px].
    Landmarks not in `positions` default to (100, 100).
    """
    return [[i, positions.get(i, (100, 100))[0],
                positions.get(i, (100, 100))[1]]
            for i in range(n)]


def make_img() -> np.ndarray:
    return np.zeros((480, 640, 3), dtype=np.uint8)


def make_detector() -> MagicMock:
    """Minimal mock — yoga_tracker.update() doesn't call detector methods."""
    return MagicMock()


# ── Idealised coordinates from yoga_angle_dryrun_v3.py ───────────────────────
# Mountain pose: all angles verified to be inside range.
MOUNTAIN_CORRECT_POSITIONS = {
    11: (560, 200), 12: (720, 200),  # L/R Shoulder
    13: (540, 310), 14: (740, 310),  # L/R Elbow
    15: (530, 420), 16: (750, 420),  # L/R Wrist
    23: (580, 360), 24: (700, 360),  # L/R Hip
    25: (575, 500), 26: (705, 500),  # L/R Knee
    27: (570, 650), 28: (710, 650),  # L/R Ankle
}

# Mountain pose with arms raised overhead — fails arm-at-side check.
MOUNTAIN_ARMS_UP_POSITIONS = {
    **MOUNTAIN_CORRECT_POSITIONS,
    13: (540, 100), 14: (740, 100),  # Elbows raised above head
    15: (530, 30),  16: (750, 30),   # Wrists raised
}

# Tree pose: correct standing leg, raised knee.
TREE_CORRECT_POSITIONS = {
    11: (570, 200), 12: (710, 200),
    13: (560, 310), 14: (720, 310),
    15: (555, 160), 16: (725, 160),
    23: (585, 360), 24: (695, 360),
    25: (580, 500), 26: (790, 430),   # R knee raised + rotated out
    27: (575, 650), 28: (620, 500),   # R ankle against standing leg
}


# ── Test 1: Correct pose held for full duration registers as completed ────────
def test_hold_completes_after_min_duration(monkeypatch):
    """
    When alignment stays above threshold for >= min_hold_secs, pose_completed
    must become True.
    """
    tracker = YogaPoseTracker("mountain_pose")
    assert tracker._min_hold == 15  # sanity-check config

    lm_list = make_lm_list(MOUNTAIN_CORRECT_POSITIONS)
    img      = make_img()
    detector = make_detector()

    # Manually force _hold_start to 16 seconds ago so the timer fires.
    monkeypatch.setattr(time, "time", lambda: 1000.0)
    tracker._hold_start = 1000.0 - 16.0  # 16 sec ago

    # Update once with correct pose (alignment >= 75)
    tracker.update(detector, img, lm_list, draw=False)

    assert tracker.alignment_score >= 75.0, (
        f"Expected alignment >= 75, got {tracker.alignment_score}"
    )
    assert tracker.is_holding_correctly is True
    assert tracker.pose_completed is True


# ── Test 2: Pose broken before min duration does NOT count ────────────────────
def test_broken_hold_does_not_complete(monkeypatch):
    """
    If alignment drops below threshold before min_hold_secs, hold timer resets
    and pose_completed stays False.
    """
    tracker = YogaPoseTracker("mountain_pose")
    img      = make_img()
    detector = make_detector()

    monkeypatch.setattr(time, "time", lambda: 1000.0)

    # First: correct pose, but only 5 sec into the hold
    correct_lm = make_lm_list(MOUNTAIN_CORRECT_POSITIONS)
    tracker._hold_start = 1000.0 - 5.0
    tracker.update(detector, img, correct_lm, draw=False)
    assert tracker.pose_completed is False   # only 5s, need 15s

    # Now break the pose (arms up — fails arm-at-side check)
    wrong_lm = make_lm_list(MOUNTAIN_ARMS_UP_POSITIONS)
    tracker.update(detector, img, wrong_lm, draw=False)

    assert tracker.is_holding_correctly is False
    assert tracker.hold_duration_secs   == 0.0
    assert tracker.pose_completed       is False


# ── Test 3: Alignment score responds to deviation ────────────────────────────
def test_alignment_score_decreases_with_deviation(monkeypatch):
    """
    Perfect textbook pose -> high alignment score.
    Deliberately wrong pose (arms raised) -> lower alignment score.
    """
    tracker  = YogaPoseTracker("mountain_pose")
    img      = make_img()
    detector = make_detector()

    monkeypatch.setattr(time, "time", lambda: 1000.0)

    correct_lm = make_lm_list(MOUNTAIN_CORRECT_POSITIONS)
    tracker.update(detector, img, correct_lm, draw=False)
    score_correct = tracker.alignment_score

    wrong_lm = make_lm_list(MOUNTAIN_ARMS_UP_POSITIONS)
    tracker2 = YogaPoseTracker("mountain_pose")
    tracker2.update(detector, img, wrong_lm, draw=False)
    score_wrong = tracker2.alignment_score

    assert score_correct > score_wrong, (
        f"Correct pose score ({score_correct}) should exceed wrong pose score ({score_wrong})"
    )
    assert score_correct >= 75.0, f"Correct pose should pass threshold, got {score_correct}"


# ── Test 4: Hold timer resets when alignment drops ────────────────────────────
def test_hold_timer_resets_on_wrong_pose(monkeypatch):
    """
    If alignment was correct for 8 sec then drops, hold_duration_secs resets to 0.
    """
    tracker  = YogaPoseTracker("mountain_pose")
    img      = make_img()
    detector = make_detector()

    monkeypatch.setattr(time, "time", lambda: 1000.0)

    # Correct pose, 8 sec in
    correct_lm = make_lm_list(MOUNTAIN_CORRECT_POSITIONS)
    tracker._hold_start = 1000.0 - 8.0
    tracker.update(detector, img, correct_lm, draw=False)
    assert tracker.hold_duration_secs >= 8.0

    # Wrong pose — timer should reset
    wrong_lm = make_lm_list(MOUNTAIN_ARMS_UP_POSITIONS)
    tracker.update(detector, img, wrong_lm, draw=False)
    assert tracker.hold_duration_secs == 0.0
    assert tracker._hold_start is None


# ── Test 5: Unknown pose key raises ValueError ────────────────────────────────
def test_unknown_pose_key_raises():
    with pytest.raises(ValueError, match="Unknown yoga pose key"):
        YogaPoseTracker("not_a_real_pose")


# ── Test 6: Empty lm_list gives score=0, no hold ──────────────────────────────
def test_empty_lm_list_gives_zero_score(monkeypatch):
    tracker  = YogaPoseTracker("mountain_pose")
    img      = make_img()
    detector = make_detector()

    monkeypatch.setattr(time, "time", lambda: 1000.0)
    tracker.update(detector, img, [], draw=False)

    assert tracker.alignment_score    == 0.0
    assert tracker.is_holding_correctly is False
    assert tracker.hold_duration_secs   == 0.0


# ── Test 7: reset_completion re-enables completion detection ──────────────────
def test_reset_completion_allows_re_trigger(monkeypatch):
    tracker  = YogaPoseTracker("mountain_pose")
    img      = make_img()
    detector = make_detector()

    monkeypatch.setattr(time, "time", lambda: 1000.0)

    # Complete the pose
    tracker._hold_start = 1000.0 - 16.0
    correct_lm = make_lm_list(MOUNTAIN_CORRECT_POSITIONS)
    tracker.update(detector, img, correct_lm, draw=False)
    assert tracker.pose_completed is True

    # Reset
    tracker.reset_completion()
    assert tracker.pose_completed       is False
    assert tracker.hold_duration_secs   == 0.0
    assert tracker._hold_start          is None

    # Complete again
    tracker._hold_start = 1000.0 - 16.0
    tracker.update(detector, img, correct_lm, draw=False)
    assert tracker.pose_completed is True


# ── Test 8: _compute_angle helper ─────────────────────────────────────────────
def test_compute_angle_known_values():
    """
    Verify _compute_angle() matches expected values from the dry-run.
    Mountain knee straight: 23->25->27 should be ~180 (verified 179.9).
    """
    lm = make_lm_list(MOUNTAIN_CORRECT_POSITIONS)
    angle = _compute_angle(lm, 23, 25, 27)
    assert 165.0 <= angle <= 180.0, f"Expected ~179.9, got {angle}"


def test_compute_angle_missing_landmark():
    """
    If a landmark index is out of range, _compute_angle returns 0.0.
    """
    lm = make_lm_list({}, n=10)   # only 10 landmarks
    angle = _compute_angle(lm, 11, 23, 25)  # indices out of range
    assert angle == 0.0


# ── Test 9: Tree pose tracker (different pose key) ────────────────────────────
def test_tree_pose_correct_alignment(monkeypatch):
    """
    Tree pose with idealised coordinates should achieve alignment >= 75%.
    """
    tracker  = YogaPoseTracker("tree_pose")
    img      = make_img()
    detector = make_detector()

    monkeypatch.setattr(time, "time", lambda: 1000.0)

    lm_list = make_lm_list(TREE_CORRECT_POSITIONS)
    tracker.update(detector, img, lm_list, draw=False)

    assert tracker.alignment_score >= 75.0, (
        f"Tree pose correct alignment expected >= 75, got {tracker.alignment_score}"
    )
