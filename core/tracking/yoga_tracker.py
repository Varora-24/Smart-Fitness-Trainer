# ================================================================
#  yoga_tracker.py  -  Hold-based yoga pose tracking
# ================================================================
#  Architecture: completely separate from ExerciseTracker.
#  Yoga is "hold this pose correctly for N seconds", not rep-counting.
#  Reuses PoseDetector for landmark extraction but has no stage machine.
# ================================================================

from __future__ import annotations

import time
import logging
import math
from typing import Any

import cv2
import numpy as np

from core.utils.config import (
    YOGA_POSE_CONFIG,
    COLOR_GREEN, COLOR_RED, COLOR_ORANGE, COLOR_WHITE,
)

logger = logging.getLogger("yoga_tracker")


def _compute_angle(lm_list: list, p1: int, p2: int, p3: int) -> float:
    """
    Compute interior angle at landmark p2 using the exact same atan2
    formula as PoseDetector.find_angle(). Returns 0.0 if any landmark
    is missing.

    lm_list: list of [landmark_id, pixel_x, pixel_y]
    """
    max_idx = max(p1, p2, p3)
    if not lm_list or max_idx >= len(lm_list):
        return 0.0
    x1, y1 = lm_list[p1][1], lm_list[p1][2]
    x2, y2 = lm_list[p2][1], lm_list[p2][2]
    x3, y3 = lm_list[p3][1], lm_list[p3][2]
    angle = math.degrees(
        math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2)
    )
    if angle < 0:
        angle += 360
    return min(angle, 360.0 - angle)


def _check_in_range(angle: float, lo: float, hi: float) -> tuple[bool, float]:
    """
    Returns (in_range, score_0_to_100).
    Score is 100 at centre of range, decays to 0 at the boundary and below.
    """
    if angle == 0.0:                       # landmark missing
        return False, 0.0
    in_range = lo <= angle <= hi
    centre = (lo + hi) / 2.0
    half   = (hi - lo) / 2.0

    if half == 0:
        return in_range, 100.0 if in_range else 0.0

    dist_from_centre = abs(angle - centre)

    if in_range:
        # 100 at centre, 80 at edge of range
        score = 100.0 - 20.0 * (dist_from_centre / half)
    else:
        # Distance beyond nearest boundary
        dist_from_edge = dist_from_centre - half
        # Decays from 80 to 0 as distance from edge grows (full decay at 2× half-range)
        score = max(0.0, 80.0 * (1.0 - dist_from_edge / (half + 1.0)))

    return in_range, score


class YogaPoseTracker:
    """
    Tracks whether the user is currently holding a specific yoga pose
    correctly, and for how long.

    - `update()` is called every frame with lm_list from PoseDetector.
    - `is_holding_correctly` is True when alignment_score >= threshold.
    - `hold_duration_secs` is the elapsed time of the CURRENT correct hold.
      Resets to 0 whenever alignment drops below threshold.
    - `pose_completed` is True once the user holds for min_hold_secs.
    """

    def __init__(self, pose_key: str) -> None:
        if pose_key not in YOGA_POSE_CONFIG:
            raise ValueError(f"Unknown yoga pose key: {pose_key!r}")
        self.pose_key  = pose_key
        self._cfg      = YOGA_POSE_CONFIG[pose_key]
        self._threshold: float = float(self._cfg["alignment_threshold"])
        self._min_hold: float  = float(self._cfg["min_hold_secs"])

        # State
        self._hold_start:       float | None = None
        self.alignment_score:   float        = 0.0
        self.pose_completed:    bool         = False
        self.active_feedback:   str          = ""   # joint-level correction message

        # Expose for overlays
        self.is_holding_correctly: bool  = False
        self.hold_duration_secs:   float = 0.0

        logger.info("YogaPoseTracker initialised for %s", pose_key)

    # ── Public API ────────────────────────────────────────────────
    def update(
        self,
        detector: Any,
        img: np.ndarray,
        lm_list: list,
        draw: bool = True,
    ) -> None:
        """
        Evaluate current alignment and update hold timer.

        Parameters
        ----------
        detector : PoseDetector instance (not directly used for angle math;
                   we call _compute_angle() directly for consistency)
        img      : BGR frame for drawing
        lm_list  : list of [id, x_px, y_px] from PoseDetector.find_position()
        draw     : overlay alignment info on img
        """
        checks = self._cfg.get("landmark_checks", [])
        if not lm_list or not checks:
            self.is_holding_correctly = False
            self.alignment_score      = 0.0
            self.active_feedback      = "Position yourself in front of the camera"
            self._reset_hold()
            return

        total_score   = 0.0
        worst_msg     = ""
        worst_score   = 100.0
        all_in_range  = True

        for check in checks:
            p1, p2, p3 = check["chain"]
            lo, hi     = check["range"]
            angle      = _compute_angle(lm_list, p1, p2, p3)
            in_range, score = _check_in_range(angle, lo, hi)

            total_score += score
            if not in_range:
                all_in_range = False
            if score < worst_score:
                worst_score = score
                worst_msg   = check.get("feedback", "Adjust your pose")

        n = len(checks)
        self.alignment_score     = round(total_score / n, 1) if n else 0.0
        self.is_holding_correctly = self.alignment_score >= self._threshold
        self.active_feedback      = worst_msg if not all_in_range else ""

        # ── Hold timer ───────────────────────────────────────────
        now = time.time()
        if self.is_holding_correctly:
            if self._hold_start is None:
                self._hold_start = now
            self.hold_duration_secs = now - self._hold_start
            if self.hold_duration_secs >= self._min_hold:
                self.pose_completed = True
        else:
            self._reset_hold()

        if draw:
            self._draw_overlay(img, lm_list)

    def reset_completion(self) -> None:
        """Allow re-triggering the completed state for a new hold."""
        self.pose_completed = False
        self._reset_hold()

    # ── Helpers ───────────────────────────────────────────────────
    def _reset_hold(self) -> None:
        self._hold_start        = None
        self.hold_duration_secs = 0.0

    def _draw_overlay(self, img: np.ndarray, lm_list: list) -> None:
        """Draw alignment score, hold-timer bar, and feedback text."""
        h, w = img.shape[:2]

        # ── Colour based on holding state ─────────────────────────
        state_color = COLOR_GREEN if self.is_holding_correctly else COLOR_ORANGE

        # ── Alignment score ──────────────────────────────────────
        score_text = f"Alignment: {self.alignment_score:.0f}%"
        cv2.putText(img, score_text, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, state_color, 3, cv2.LINE_AA)

        # ── Hold-timer bar ────────────────────────────────────────
        bar_x1, bar_y1 = 20, 80
        bar_x2, bar_y2 = 320, 110
        cv2.rectangle(img, (bar_x1, bar_y1), (bar_x2, bar_y2),
                      (60, 60, 60), -1)
        prog = min(self.hold_duration_secs / max(self._min_hold, 1.0), 1.0)
        fill_x = int(bar_x1 + prog * (bar_x2 - bar_x1))
        cv2.rectangle(img, (bar_x1, bar_y1), (fill_x, bar_y2),
                      state_color, -1)
        hold_text = (f"Hold: {self.hold_duration_secs:.1f}s / {self._min_hold:.0f}s"
                     if self.is_holding_correctly else
                     f"Hold: {self._min_hold:.0f}s needed")
        cv2.putText(img, hold_text, (bar_x1 + 5, bar_y2 - 7),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_WHITE, 1, cv2.LINE_AA)

        # ── Feedback cue ─────────────────────────────────────────
        if self.active_feedback:
            cv2.putText(img, self.active_feedback, (20, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, COLOR_RED, 2, cv2.LINE_AA)

        # ── Completion flash ─────────────────────────────────────
        if self.pose_completed:
            cv2.putText(img, "POSE COMPLETE!", (w // 2 - 130, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_GREEN, 4, cv2.LINE_AA)
