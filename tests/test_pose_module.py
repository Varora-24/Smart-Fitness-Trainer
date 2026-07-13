import pytest  # noqa: F401
import numpy as np
from unittest.mock import MagicMock, patch
from pose_module import PoseDetector

class MockLandmark:
    def __init__(self, x, y, z=0, visibility=1.0, presence=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility
        self.presence = presence

class MockPoseLandmarks:
    def __init__(self, landmarks):
        self.pose_landmarks = [landmarks]

@patch("mediapipe.tasks.python.vision.PoseLandmarker.create_from_options")
@patch("mediapipe.tasks.python.BaseOptions")
def test_pose_detector_initializes_with_model_file(mock_base_options, mock_create):
    """Test that PoseDetector uses the correct configuration and model path."""
    detector = PoseDetector()
    
    # Assert model path passed to BaseOptions
    mock_base_options.assert_called_with(model_asset_path="models/pose_landmarker_lite.task")
    assert mock_create.called
    assert detector._frame_timestamp_ms == 0
    # Must initialise results and lm_list
    assert detector.lm_list == []
    assert detector.results is not None
    assert detector.results.pose_landmarks is None

@patch("mediapipe.tasks.python.vision.PoseLandmarker.create_from_options")
def test_find_pose_empty_result_returns_none_shim(mock_create):
    """
    CRITICAL SHIM BEHAVIOR TEST:
    If the detector returns an empty result (no pose detected), the shim MUST explicitly set 
    self.results.pose_landmarks to None so that downstream truthiness checks match legacy behaviour exactly.
    """
    detector = PoseDetector()
    
    # Mock detect_for_video to return an empty result
    empty_result = MagicMock()
    empty_result.pose_landmarks = []
    detector._detector.detect_for_video.return_value = empty_result
    
    # Create a dummy image
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Run find_pose
    detector.find_pose(dummy_img, draw=False)
    
    # Truthiness of pose_landmarks MUST be falsy (None)
    assert detector.results is not None
    assert detector.results.pose_landmarks is None
    
    # Should safely return an empty list
    lm_list = detector.find_position(dummy_img, draw=False)
    assert lm_list == []

@patch("mediapipe.tasks.python.vision.PoseLandmarker.create_from_options")
def test_find_position_returns_correct_shape(mock_create):
    """Test that find_position returns the list in the exact [id, x, y] shape."""
    detector = PoseDetector()
    
    # Setup mock result with 3 dummy landmarks
    mock_lms = [
        MockLandmark(x=0.1, y=0.2), # id=0, at (10, 20) in 100x100
        MockLandmark(x=0.3, y=0.4), # id=1, at (30, 40)
        MockLandmark(x=0.5, y=0.6)  # id=2, at (50, 60)
    ]
    mock_result = MockPoseLandmarks(mock_lms)
    detector._detector.detect_for_video.return_value = mock_result
    
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    detector.find_pose(dummy_img, draw=False)
    
    lm_list = detector.find_position(dummy_img, draw=False)
    
    # Verify shape and scaling
    assert len(lm_list) == 3
    assert lm_list[0] == [0, 10, 20]
    assert lm_list[1] == [1, 30, 40]
    assert lm_list[2] == [2, 50, 60]

@patch("mediapipe.tasks.python.vision.PoseLandmarker.create_from_options")
def test_find_angle_matches_known_geometry(mock_create):
    """Test find_angle computes the correct degree angle between three points."""
    detector = PoseDetector()
    
    # Let's create a perfect 90 degree angle (right angle)
    # p1 at (100, 0)
    # p2 at (0, 0) - vertex
    # p3 at (0, 100)
    mock_lms = [
        MockLandmark(x=1.0, y=0.0), # p1 (id 0) - Right
        MockLandmark(x=0.0, y=0.0), # p2 (id 1) - Vertex at Origin
        MockLandmark(x=0.0, y=1.0)  # p3 (id 2) - Down
    ]
    mock_result = MockPoseLandmarks(mock_lms)
    detector._detector.detect_for_video.return_value = mock_result
    
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    detector.find_pose(dummy_img, draw=False)
    detector.find_position(dummy_img, draw=False)
    
    # Calculate angle at vertex p2 (index 1) between p1 (index 0) and p3 (index 2)
    angle = detector.find_angle(dummy_img, 0, 1, 2, draw=False)
    
    # Should be exactly 90 degrees
    assert angle == 90.0

@patch("mediapipe.tasks.python.vision.PoseLandmarker.create_from_options")
def test_find_angle_missing_landmarks_returns_zero(mock_create):
    """Ensure find_angle returns 0.0 if not enough landmarks are detected."""
    detector = PoseDetector()
    
    # Only 2 landmarks detected
    mock_lms = [MockLandmark(x=0.0, y=0.0), MockLandmark(x=1.0, y=1.0)]
    mock_result = MockPoseLandmarks(mock_lms)
    detector._detector.detect_for_video.return_value = mock_result
    
    dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
    detector.find_pose(dummy_img, draw=False)
    detector.find_position(dummy_img, draw=False)
    
    # Asking for an angle using a missing landmark (index 2)
    angle = detector.find_angle(dummy_img, 0, 1, 2, draw=False)
    assert angle == 0.0
