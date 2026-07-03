# ============================================================
#  pose_module.py  –  MediaPipe Pose wrapper
# ============================================================
# Wraps Google's MediaPipe Pose into a reusable class.
# Provides: pose detection, landmark extraction, angle maths.

import cv2
import mediapipe as mp
import math
import numpy as np
from typing import Any
from config import (
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE,
    MODEL_COMPLEXITY,
)


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
        self._mp_draw = mp.solutions.drawing_utils
        self._mp_pose = mp.solutions.pose

        # Initialise the MediaPipe Pose solution
        self.pose = self._mp_pose.Pose(
            static_image_mode       = static_image_mode,
            model_complexity        = model_complexity,
            smooth_landmarks        = smooth_landmarks,
            enable_segmentation     = False,
            min_detection_confidence= detection_con,
            min_tracking_confidence = tracking_con,
        )

        # Will be populated by find_pose() on every frame
        self.results  : Any = None
        self.lm_list  : list[list[int]] = []

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
        self.results = self.pose.process(img_rgb)

        if self.results is not None and self.results.pose_landmarks and draw:
            self._mp_draw.draw_landmarks(
                img,
                self.results.pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS,
            )
        return img

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

        if draw:
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
