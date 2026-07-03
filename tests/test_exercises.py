# ================================================================
#  tests/test_exercises.py  –  Unit tests for exercise tracking
# ================================================================

from unittest.mock import MagicMock
from exercises import ExerciseTracker

class MockPoseDetector:
    def __init__(self, visible=True):
        self.results = MagicMock()
        if visible:
            self.results.pose_landmarks = MagicMock()
            landmark_mocks = []
            for _ in range(33):
                lm = MagicMock()
                lm.visibility = 1.0
                landmark_mocks.append(lm)
            self.results.pose_landmarks.landmark = landmark_mocks
        else:
            self.results.pose_landmarks = None

    def find_angle(self, img, p1, p2, p3, draw=True):
        return 120.0

    def find_position(self, img, draw=False):
        return [[i, 50, 100] for i in range(33)]

# ── Test 1.1: Reset bad_posture each frame ──────────────────────
def test_bad_posture_reset():
    tracker = ExerciseTracker("squats")
    detector = MockPoseDetector()
    img = MagicMock()
    lm_list = detector.find_position(img)
    
    # 1. Set bad_posture manually to True
    tracker.bad_posture = True
    
    # 2. Call update with valid posture
    tracker.update(detector, img, lm_list, draw=False)
    
    # bad_posture should have reset to False
    assert tracker.bad_posture is False

# ── Test 1.2: Save last_rep_rom_score etc. ────────────────────
def test_last_rep_attributes_saved():
    tracker = ExerciseTracker("squats")
    tracker._sym_samples = [100.0]
    tracker._posture_samples = [100.0]
    tracker._velocity_samples = [100.0]
    tracker._rep_min_angle = 90.0
    
    tracker._finish_rep()
    
    assert tracker.last_rep_rom_score == 100.0
    assert tracker.last_rep_control_score == 100.0
    assert tracker.last_rep_was_clean is True
    assert tracker.last_rep_min_angle == 90.0
    assert tracker._rep_min_angle == 360.0

# ── Test 1.7: Inverted percentage for shoulder_press ────────────
def test_depth_direction_percentage():
    # 1. Down direction (squats: angle range 90-170, bottom = small angle = 100% depth)
    tracker_squats = ExerciseTracker("squats")
    detector_squats = MockPoseDetector()
    # Mock find_angle for squats to return 90.0 (fully down)
    detector_squats.find_angle = MagicMock(return_value=90.0)
    lm_list = [[i, 0, 0] for i in range(33)]
    
    tracker_squats.update(detector_squats, MagicMock(), lm_list, draw=False)
    assert tracker_squats.percentage >= 95.0
    
    # 2. Up direction (shoulder_press: angle range 80-170, top = large angle = 100% extension)
    tracker_sp = ExerciseTracker("shoulder_press")
    detector_sp = MockPoseDetector()
    detector_sp.find_angle = MagicMock(return_value=170.0) # arms fully extended
    
    tracker_sp.update(detector_sp, MagicMock(), lm_list, draw=False)
    assert tracker_sp.percentage >= 95.0

# ── Test 2.3: Relative posture baseline for curls ────────────────
def test_curl_posture_baseline_delta():
    tracker = ExerciseTracker("curls")
    detector = MockPoseDetector()
    lm_list = [[i, 0, 0] for i in range(33)]
    
    # Frame 1: Set baseline to 15.0
    detector.find_angle = MagicMock(side_effect=[120.0, 120.0, 15.0, 15.0])
    tracker.update(detector, MagicMock(), lm_list, draw=False)
    assert tracker._posture_baseline == 15.0
    assert tracker.bad_posture is False
    
    # Frame 2: Subsequent frame within delta (smoothed value: (15 + 25)/2 = 20, delta = 5 <= 20)
    detector.find_angle = MagicMock(side_effect=[120.0, 120.0, 25.0, 25.0])
    tracker.update(detector, MagicMock(), lm_list, draw=False)
    assert tracker.bad_posture is False
    
    # Frame 3: Exceeding delta (smoothed value: (15 + 25 + 100)/3 = 46.67, delta = 31.67 > 20)
    detector.find_angle = MagicMock(side_effect=[120.0, 120.0, 100.0, 100.0])
    tracker.update(detector, MagicMock(), lm_list, draw=False)
    assert tracker.bad_posture is True
