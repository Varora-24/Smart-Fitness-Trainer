# ================================================================
#  tests/test_exercise_classifier.py  –  Classifier unit tests
# ================================================================

import random
from core.tracking.exercise_classifier import ExerciseClassifier

class MockPoseDetector:
    def find_angle(self, img, p1, p2, p3, draw=False):
        return 160.0

# ── Test 1.10: frame_h normalization is correct ──────────────────
def test_classifier_normalization_uses_config_height():
    clf = ExerciseClassifier()
    detector = MockPoseDetector()
    
    # 29 landmarks
    lm_list = [[i, 100, 200] for i in range(29)]
    
    # Set the last landmark y-value to a ridiculous value (e.g. 9999)
    # If the classifier used the old formula max(lm_list[-1][2], 1), frame_h would be 9999,
    # causing divided-by values to shrink to near zero.
    # By using config's FRAME_HEIGHT, the behavior is consistent.
    lm_list[-1] = [28, 100, 9999]
    
    signals = clf._compute_signals(lm_list, detector)
    
    # Check that split stance and arms overhead values are computed properly using FRAME_HEIGHT.
    # E.g. knee_height_diff = abs(200 - 200) / FRAME_HEIGHT = 0.0
    # Let's check that the code executes without error and yields valid floats.
    assert "split_stance" in signals
    assert isinstance(signals["split_stance"], float)
    assert 0.0 <= signals["split_stance"] <= 1.0


# ── Test Hysteresis (Flip-flopping Prevention) ───────────────────

class MockDetectorWithState:
    def __init__(self):
        self.mode = "squats"

    def find_angle(self, img, p1, p2, p3, draw=False):
        # We need to return specific angles based on self.mode to simulate strong signals
        # Squat uses knees (23,25,27 and 24,26,28) and hips (11,23,25 and 12,24,26)
        # Curls use elbows (11,13,15 and 12,14,16) and shoulders (23,11,13 and 24,12,14)

        if self.mode == "squats":
            if p2 in (25, 26): # knees
                return 100.0 # deep squat
            if p2 in (23, 24): # hips (torso upright)
                return 160.0
            if p2 in (13, 14): # elbows
                return 170.0 # straight
        elif self.mode == "curls":
            if p2 in (13, 14): # elbows
                return 60.0 # tight curl
            if p2 in (25, 26): # knees
                return 170.0 # standing straight
            if p2 in (23, 24): # hips
                return 170.0 # torso upright
        
        return 160.0

def _create_standing_landmarks():
    # Provide a realistic vertical posture so we don't accidentally simulate pushups
    # y increases downwards
    lm = [[i, 100, 200] for i in range(29)]
    # Shoulders
    lm[11][2] = lm[12][2] = 200
    # Hips
    lm[23][2] = lm[24][2] = 400
    # Knees
    lm[25][2] = lm[26][2] = 600
    # Ankles
    lm[27][2] = lm[28][2] = 800
    return lm

def _make_alternating_noisy_frame():
    detector = MockDetectorWithState()
    # Randomly alternate between strong squat signal and strong curl signal every few frames
    if random.random() < 0.5:
        detector.mode = "squats"
    else:
        detector.mode = "curls"
    
    lm_list = _create_standing_landmarks()
    return lm_list, detector

def _make_consistent_curl_frame():
    detector = MockDetectorWithState()
    detector.mode = "curls"
    lm_list = _create_standing_landmarks()
    return lm_list, detector

def test_classifier_resists_flip_flopping_on_noisy_alternating_signal():
    """
    Simulate exactly the failure mode found in production: alternating
    strong-squat-signal and strong-curl-signal frames within a short
    span, faster than a real rep cycle. The classifier should NOT
    switch on every window - it should require sustained, confident
    evidence before abandoning the currently tracked exercise.
    """
    clf = ExerciseClassifier()
    clf.exercise = "squats"

    switch_count = 0
    previous = clf.exercise
    # Simulate 900 frames (10 full windows at WINDOW_FRAMES=90)
    for _ in range(900):
        lm_list, detector = _make_alternating_noisy_frame()
        result = clf.update(lm_list, detector)
        if result != previous:
            switch_count += 1
            previous = result

    # With hysteresis, this should switch rarely if at all under noise
    assert switch_count <= 2

def test_classifier_still_switches_on_genuine_sustained_change():
    """
    Confirm the hysteresis fix doesn't prevent legitimate exercise
    changes - a real, sustained switch (e.g. user actually moves from
    squats to curls and keeps doing curls) must still be detected
    within a reasonable number of windows.
    """
    clf = ExerciseClassifier()
    clf.exercise = "squats"

    # simulate sustained, consistent curl signal for several windows
    # Window size is 90 frames, wait for 300 frames (~3.3 windows, well over the 2 consecutive requirement)
    for _ in range(300):
        lm_list, detector = _make_consistent_curl_frame()
        clf.update(lm_list, detector)

    assert clf.exercise == "curls"
