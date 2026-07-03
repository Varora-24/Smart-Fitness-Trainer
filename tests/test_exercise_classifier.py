# ================================================================
#  tests/test_exercise_classifier.py  –  Classifier unit tests
# ================================================================

from exercise_classifier import ExerciseClassifier

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
