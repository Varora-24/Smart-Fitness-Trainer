import time
import pytest
import numpy as np
from core.tracking.surya_namaskar_tracker import SuryaNamaskarTracker, SURYA_NAMASKAR_STEPS

def test_surya_namaskar_init():
    tracker = SuryaNamaskarTracker()
    assert tracker.step_idx == 0
    assert not tracker.sequence_completed
    assert tracker.current_step_config["name"] == "1. Prayer Pose"

def test_fallback_step_auto_advancement():
    tracker = SuryaNamaskarTracker()
    # Move manually to a fallback step (Step 3: Hand-to-Foot Pose)
    tracker.step_idx = 2
    assert tracker.current_step_config["mode"] == "fallback"
    
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # On first update, hold_start is set and score is 100
    tracker.update(None, img, [], draw=True)
    assert tracker.alignment_score == 100.0
    assert tracker.is_holding_correctly is True
    
    # Simulate time passing beyond duration (5.0s)
    tracker._hold_start = time.time() - 5.5
    tracker.update(None, img, [], draw=True)
    
    # Should have advanced to Step 4 (Equestrian Pose Left)
    assert tracker.step_idx == 3
    assert tracker.current_step_config["name"] == "4. Equestrian Pose (Left leg forward)"

def test_strict_lunge_double_bend_rejection():
    """Verify that a double-bent knee stance fails Equestrian Pose check."""
    tracker = SuryaNamaskarTracker()
    tracker.step_idx = 3 # Equestrian Pose Left (Step 4)
    assert tracker.current_step_config["mode"] == "strict"
    
    # Create fake landmarks where both left knee (23,25,27) and right knee (24,26,28) are bent (90 deg)
    # 33 landmarks needed
    lm_list = [[i, 100, 100] for i in range(33)]
    
    # Left hip=23, knee=25, ankle=27 -> create 90 degree bend
    lm_list[23] = [23, 100, 100]
    lm_list[25] = [25, 100, 200]
    lm_list[27] = [27, 200, 200] # vector (0, 100) and (100, 0) -> 90 deg
    
    # Right hip=24, knee=26, ankle=28 -> ALSO create 90 degree bend (double-bent lunge)
    lm_list[24] = [24, 100, 100]
    lm_list[26] = [26, 100, 200]
    lm_list[28] = [28, 200, 200]
    
    # Torso (11, 23, 25) upright
    lm_list[11] = [11, 100, 0]
    
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    tracker.update(None, img, lm_list, draw=True)
    
    # Should NOT be holding correctly because right back leg is not straight (range 155-180)
    assert tracker.is_holding_correctly is False
    assert "Straighten your back (right) leg completely!" in tracker.active_feedback

def test_sequence_completion():
    tracker = SuryaNamaskarTracker()
    tracker.step_idx = len(SURYA_NAMASKAR_STEPS) - 1 # Last step (12)
    
    # Force complete
    tracker.advance_step()
    assert tracker.sequence_completed is True
    assert tracker.total_completed_rounds == 1
    
    # Calling update on completed tracker should do nothing
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    tracker.update(None, img, [], draw=True)
    assert tracker.sequence_completed is True
