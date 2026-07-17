# ============================================================
#  pose_module.py  –  MediaPipe Pose wrapper
# ============================================================
# Wraps Google's MediaPipe Pose into a reusable class.
# Provides: pose detection, landmark extraction, angle maths.

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import math
import numpy as np
from typing import Any
from config import (
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE,
    MODEL_COMPLEXITY,
)

# Standard 33-point Pose Connections
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
]

class PoseLandmarksShim:
    """Shim to mimic the legacy protobuf structure for a single pose."""
    def __init__(self, landmark_list):
        self.landmark = landmark_list

class ResultsShim:
    """Shim to mimic the legacy `results.pose_landmarks` access."""
    def __init__(self, pose_landmarks=None):
        self.pose_landmarks = pose_landmarks

class PoseDetector:
    """
    Thin, reusable wrapper around MediaPipe Pose.

    Usage:
        detector = PoseDetector()
        img       = detector.find_pose(img)
        lm_list   = detector.find_position(img)
        angle     = detector.find_angle(img, p1, p2, p3)
    """

    def __init__(
        self,
        static_image_mode   : bool  = False,
        model_complexity    : int   = MODEL_COMPLEXITY,
        smooth_landmarks    : bool  = True,
        detection_con       : float = DETECTION_CONFIDENCE,
        tracking_con        : float = TRACKING_CONFIDENCE,
    ):
        model_path = "models/pose_landmarker_lite.task"
        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        
        # Use VIDEO running mode for speed, but rely on high tracking confidence to force re-detection if stuck
        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=detection_con,
            min_pose_presence_confidence=detection_con,
            min_tracking_confidence=tracking_con,
            output_segmentation_masks=False
        )
        self._detector = mp_vision.PoseLandmarker.create_from_options(options)
        self._frame_timestamp_ms = 0
        
        # Will be populated by find_pose() on every frame
        self.results : Any = ResultsShim()
        self.lm_list : list[list[int]] = []

    # ----------------------------------------------------------
    def find_pose(self, img: "np.ndarray", draw: bool = True) -> "np.ndarray":
        """
        Run pose estimation on *img*.

        Parameters
        ----------
        img  : BGR image (numpy array from OpenCV)
        draw : Whether to overlay the skeleton on the image

        Returns
        -------
        img with optional skeleton overlay
        """
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        raw_result = self._detector.detect_for_video(mp_image, self._frame_timestamp_ms)
        self._frame_timestamp_ms += 33  # Assuming ~30fps 
        
        # Construct the shim: strictly set pose_landmarks to None if empty
        if raw_result and raw_result.pose_landmarks:
            self.results = ResultsShim(PoseLandmarksShim(raw_result.pose_landmarks[0]))
        else:
            self.results = ResultsShim(None)

        if draw and self.results.pose_landmarks:
            self._draw_landmarks(img, self.results.pose_landmarks.landmark)
            
        return img

    def _draw_landmarks(self, img: "np.ndarray", landmarks: list):
        """Draw landmarks and connections using OpenCV primitives."""
        h, w, _ = img.shape
        
        # Draw connections
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start = landmarks[start_idx]
                end = landmarks[end_idx]
                # Only draw if visibility is reasonable
                if getattr(start, 'visibility', 1.0) > 0.1 and getattr(end, 'visibility', 1.0) > 0.1:
                    cv2.line(img, (int(start.x * w), int(start.y * h)), 
                             (int(end.x * w), int(end.y * h)), (255, 255, 255), 2)
                    
        # Draw joints
        for lm in landmarks:
            if getattr(lm, 'visibility', 1.0) > 0.1:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(img, (cx, cy), 4, (0, 255, 0), -1)

    # ----------------------------------------------------------
    def find_position(
        self, img: "np.ndarray", draw: bool = False
    ) -> list:
        """
        Extract pixel coordinates for every detected landmark.

        Returns
        -------
        list of [landmark_id, pixel_x, pixel_y]
        An empty list when no pose is detected.
        """
        self.lm_list = []

        if self.results is None or not self.results.pose_landmarks:
            return self.lm_list

        h, w, _ = img.shape
        for idx, lm in enumerate(self.results.pose_landmarks.landmark):
            cx, cy = int(lm.x * w), int(lm.y * h)
            self.lm_list.append([idx, cx, cy])
            if draw:
                cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)

        return self.lm_list

    # ----------------------------------------------------------
    def find_angle(
        self,
        img: "np.ndarray",
        p1 : int,
        p2 : int,
        p3 : int,
        draw: bool = True,
    ) -> float:
        """
        Compute the angle (in degrees) at landmark *p2*
        formed by the line p1-p2-p3.

        Parameters
        ----------
        p1, p2, p3 : MediaPipe landmark indices
        draw       : Overlay angle lines and circles on *img*

        Returns
        -------
        Angle in degrees [0, 360).
        Returns 0 if any landmark is missing.
        """
        # Safety – make sure all three landmarks exist
        if not self.lm_list or max(p1, p2, p3) >= len(self.lm_list):
            return 0.0

        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        x3, y3 = self.lm_list[p3][1], self.lm_list[p3][2]

        # atan2 gives signed angle; normalise to [0, 360)
        angle = math.degrees(
            math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2)
        )
        if angle < 0:
            angle += 360

        if draw and img is not None:
            self._draw_angle_overlay(img, x1, y1, x2, y2, x3, y3)

        return angle

    # ----------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------
    def _draw_angle_overlay(self, img, x1, y1, x2, y2, x3, y3):
        """Draw the three joint circles and connecting lines."""
        # Lines between joints
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 3)
        cv2.line(img, (x3, y3), (x2, y2), (255, 255, 255), 3)

        # Outer ring + filled dot at each joint
        for cx, cy in [(x1, y1), (x2, y2), (x3, y3)]:
            cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 15, (0, 0, 255), 2)
