# ================================================================
#  surya_namaskar_tracker.py - Guided Sun Salutation Sequence
# ================================================================
#  Implements the 12-step Surya Namaskar sequence with a hybrid
#  advancement model:
#  - Strict Form: requires alignment score >= threshold held for N secs.
#  - Timed Fallback: advances automatically on duration interval for
#    floor/prone postures occluded from a single front-facing camera.
# ================================================================

from __future__ import annotations
import time
import math
from typing import Any
import cv2
import numpy as np

from core.utils.config import COLOR_GREEN, COLOR_ORANGE, COLOR_WHITE

SURYA_NAMASKAR_STEPS: list[dict[str, Any]] = [
    {
        "name": "1. Prayer Pose",
        "sanskrit": "Pranamasana",
        "mode": "strict",
        "duration": 5.0,
        "alignment_threshold": 70.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Yoga_Tadasana.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 3.0)",
        "description": "Stand tall with hands together near your chest.",
        "landmark_checks": [
            # Stand upright, legs straight
            {"chain": (23, 25, 27), "range": (160, 180), "feedback": "Straighten your left leg"},
            {"chain": (24, 26, 28), "range": (160, 180), "feedback": "Straighten your right leg"},
            {"chain": (25, 23, 11), "range": (155, 180), "feedback": "Stand tall"},
            {"chain": (26, 24, 12), "range": (155, 180), "feedback": "Stand tall"},
            # Arms bent near torso/chest for prayer hands
            {"chain": (11, 13, 15), "range": (20, 140), "feedback": "Bring palms together at chest"},
            {"chain": (12, 14, 16), "range": (20, 140), "feedback": "Bring palms together at chest"},
        ],
        "cue": "Inhale, exhale: bringing palms together in prayer position at chest height.",
    },
    {
        "name": "2. Raised Arms Pose",
        "sanskrit": "Hastauttasana",
        "mode": "strict",
        "duration": 5.0,
        "alignment_threshold": 75.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/59/Utkatasana_Yoga-Asana_Nina-Mel.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 4.0) [Overhead Arms Reference]",
        "description": "Lift arms overhead and stretch slightly upward/back.",
        "landmark_checks": [
            {"chain": (23, 11, 13), "range": (135, 180), "feedback": "Reach both arms fully overhead"},
            {"chain": (24, 12, 14), "range": (135, 180), "feedback": "Reach both arms fully overhead"},
            {"chain": (11, 13, 15), "range": (150, 180), "feedback": "Straighten your elbows overhead"},
            {"chain": (12, 14, 16), "range": (150, 180), "feedback": "Straighten your elbows overhead"},
        ],
        "cue": "Inhale: stretch arms up and over, lengthening the spine.",
    },
    {
        "name": "3. Hand-to-Foot Pose",
        "sanskrit": "Uttanasana",
        "mode": "fallback",
        "duration": 5.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Trikonasana_Yoga-Asana_Nina-Mel.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 4.0) [Forward Fold Reference]",
        "description": "Exhale and fold forward from the waist, bringing hands down toward the floor.",
        "cue": "Exhale: bend forward from hips, fingers down toward toes. (Guided Timed Hold)",
    },
    {
        "name": "4. Equestrian Pose (Left leg forward)",
        "sanskrit": "Ashwa Sanchalanasana",
        "mode": "strict",
        "duration": 6.0,
        "alignment_threshold": 70.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/84/Virabhadrasana_II_Yoga-Asana_Nina-Mel.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 4.0) [Lunge Reference]",
        "description": "Step right foot back into a lunge, left foot forward between palms.",
        "landmark_checks": [
            # CRITICAL CHECK: Bent leg is bent AND opposite leg is straight! Double-bent lunge must fail!
            {"chain": (23, 25, 27), "range": (70, 135), "feedback": "Bend your front (left) knee more into a lunge"},
            {"chain": (24, 26, 28), "range": (155, 180), "feedback": "Straighten your back (right) leg completely!"},
            {"chain": (11, 23, 25), "range": (60, 160), "feedback": "Keep torso extended over lunge stance"},
        ],
        "cue": "Inhale: step right leg straight back into lunge, front left knee bent.",
    },
    {
        "name": "5. Stick Pose (Plank)",
        "sanskrit": "Dandasana",
        "mode": "fallback",
        "duration": 6.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Pushup_-_1.png",
        "image_source": "Wikimedia Commons (CC BY-SA 3.0)",
        "description": "Step left leg back beside right leg; keep entire body straight like a pushup plank.",
        "cue": "Retain breath: step left foot back into high plank position. (Guided Timed Hold)",
    },
    {
        "name": "6. Eight-Limbed Pose",
        "sanskrit": "Ashtanga Namaskara",
        "mode": "fallback",
        "duration": 5.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c5/Pushup_-_1.png",
        "image_source": "Wikimedia Commons (CC BY-SA 3.0) [Prone Depth Reference]",
        "description": "Gently drop knees, chest, and chin to the floor while hips remain slightly lifted.",
        "cue": "Exhale: lower knees, chest, and chin to the ground. (Guided Timed Hold)",
    },
    {
        "name": "7. Cobra Pose",
        "sanskrit": "Bhujangasana",
        "mode": "fallback",
        "duration": 6.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/62/Seated-military-shoulder-press-1.png",
        "image_source": "Wikimedia Commons (CC BY-SA 3.0) [Torso Extension Reference]",
        "description": "Slide forward and arch chest upward into cobra, keeping elbows slightly bent.",
        "cue": "Inhale: lift chest into Cobra pose, gaze forward and up. (Guided Timed Hold)",
    },
    {
        "name": "8. Mountain / Down Dog",
        "sanskrit": "Parvatasana / Adho Mukha Svanasana",
        "mode": "fallback",
        "duration": 6.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/57/Downward-Facing-Dog.JPG",
        "image_source": "Wikimedia Commons (Public Domain / CC BY-SA)",
        "description": "Lift hips upward into an inverted-V shape, pushing heels toward floor.",
        "cue": "Exhale: tuck toes, raise hips high into Downward-Facing Dog. (Guided Timed Hold)",
    },
    {
        "name": "9. Equestrian Pose (Right leg forward)",
        "sanskrit": "Ashwa Sanchalanasana",
        "mode": "strict",
        "duration": 6.0,
        "alignment_threshold": 70.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/84/Virabhadrasana_II_Yoga-Asana_Nina-Mel.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 4.0) [Lunge Reference]",
        "description": "Step right foot forward between palms, left leg extended straight back.",
        "landmark_checks": [
            # CRITICAL CHECK: Bent right knee AND straight left back leg!
            {"chain": (24, 26, 28), "range": (70, 135), "feedback": "Bend your front (right) knee more into a lunge"},
            {"chain": (23, 25, 27), "range": (155, 180), "feedback": "Straighten your back (left) leg completely!"},
            {"chain": (12, 24, 26), "range": (60, 160), "feedback": "Keep torso extended over lunge stance"},
        ],
        "cue": "Inhale: step right foot forward between hands, left leg straight behind.",
    },
    {
        "name": "10. Hand-to-Foot Pose",
        "sanskrit": "Uttanasana",
        "mode": "fallback",
        "duration": 5.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/9/9d/Trikonasana_Yoga-Asana_Nina-Mel.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 4.0) [Forward Fold Reference]",
        "description": "Step left foot forward beside right foot, folding forward over both legs.",
        "cue": "Exhale: bring left leg forward to join right, folding at the hips. (Guided Timed Hold)",
    },
    {
        "name": "11. Raised Arms Pose",
        "sanskrit": "Hastauttasana",
        "mode": "strict",
        "duration": 5.0,
        "alignment_threshold": 75.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/59/Utkatasana_Yoga-Asana_Nina-Mel.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 4.0) [Overhead Arms Reference]",
        "description": "Rise up smoothly with arms extended overhead.",
        "landmark_checks": [
            {"chain": (23, 11, 13), "range": (135, 180), "feedback": "Reach both arms fully overhead"},
            {"chain": (24, 12, 14), "range": (135, 180), "feedback": "Reach both arms fully overhead"},
            {"chain": (11, 13, 15), "range": (150, 180), "feedback": "Straighten your elbows overhead"},
            {"chain": (12, 14, 16), "range": (150, 180), "feedback": "Straighten your elbows overhead"},
        ],
        "cue": "Inhale: sweep arms overhead and extend upward.",
    },
    {
        "name": "12. Prayer Pose",
        "sanskrit": "Pranamasana",
        "mode": "strict",
        "duration": 5.0,
        "alignment_threshold": 70.0,
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e5/Yoga_Tadasana.jpg",
        "image_source": "Wikimedia Commons (CC BY-SA 3.0)",
        "description": "Return to standing upright with palms joined together at chest.",
        "landmark_checks": [
            {"chain": (23, 25, 27), "range": (160, 180), "feedback": "Straighten your left leg"},
            {"chain": (24, 26, 28), "range": (160, 180), "feedback": "Straighten your right leg"},
            {"chain": (25, 23, 11), "range": (155, 180), "feedback": "Stand tall"},
            {"chain": (26, 24, 12), "range": (155, 180), "feedback": "Stand tall"},
            {"chain": (11, 13, 15), "range": (20, 140), "feedback": "Bring palms together at chest"},
            {"chain": (12, 14, 16), "range": (20, 140), "feedback": "Bring palms together at chest"},
        ],
        "cue": "Exhale: lower hands to heart center in prayer position to complete sequence!",
    },
]


def _compute_angle(lm_list: list, p1: int, p2: int, p3: int) -> float:
    max_idx = max(p1, p2, p3)
    if not lm_list or max_idx >= len(lm_list):
        return 0.0
    x1, y1 = lm_list[p1][1], lm_list[p1][2]
    x2, y2 = lm_list[p2][1], lm_list[p2][2]
    x3, y3 = lm_list[p3][1], lm_list[p3][2]
    angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
    if angle < 0:
        angle += 360
    return min(angle, 360.0 - angle)


def _check_in_range(angle: float, lo: float, hi: float) -> tuple[bool, float]:
    if angle == 0.0:
        return False, 0.0
    in_range = lo <= angle <= hi
    centre = (lo + hi) / 2.0
    half = (hi - lo) / 2.0

    if half == 0:
        return in_range, 100.0 if in_range else 0.0

    dist_from_centre = abs(angle - centre)
    if in_range:
        score = 100.0 - 20.0 * (dist_from_centre / half)
    else:
        dist_from_edge = dist_from_centre - half
        score = max(0.0, 80.0 * (1.0 - dist_from_edge / (half + 1.0)))

    return in_range, score


class SuryaNamaskarTracker:
    """
    Manages progression across the 12 Surya Namaskar postures.
    """

    def __init__(self) -> None:
        self.step_idx: int = 0
        self.sequence_completed: bool = False
        self.total_completed_rounds: int = 0
        self.reset_step_state()

    def reset_step_state(self) -> None:
        self._hold_start: float | None = None
        self.alignment_score: float = 0.0
        self.hold_duration_secs: float = 0.0
        self.is_holding_correctly: bool = False
        self.active_feedback: str = ""

    @property
    def current_step_config(self) -> dict[str, Any]:
        return SURYA_NAMASKAR_STEPS[self.step_idx]

    def reset_sequence(self) -> None:
        self.step_idx = 0
        self.sequence_completed = False
        self.reset_step_state()

    def update(
        self,
        detector: Any,
        img: np.ndarray,
        lm_list: list,
        draw: bool = True,
    ) -> None:
        if self.sequence_completed:
            return

        cfg = self.current_step_config
        mode = cfg["mode"]
        target_duration = cfg["duration"]
        now = time.time()

        if mode == "strict":
            checks = cfg.get("landmark_checks", [])
            if not lm_list or len(lm_list) < 29 or not checks:
                self.alignment_score = 0.0
                self.is_holding_correctly = False
                self._hold_start = None
                self.hold_duration_secs = 0.0
                self.active_feedback = "Step into frame so entire body is visible"
            else:
                total_score = 0.0
                failing_feedbacks: list[str] = []

                for chk in checks:
                    p1, p2, p3 = chk["chain"]
                    lo, hi = chk["range"]
                    ang = _compute_angle(lm_list, p1, p2, p3)
                    in_r, sc = _check_in_range(ang, lo, hi)
                    total_score += sc
                    if not in_r:
                        failing_feedbacks.append(chk["feedback"])

                self.alignment_score = total_score / max(len(checks), 1)
                thresh = cfg.get("alignment_threshold", 75.0)
                self.is_holding_correctly = (self.alignment_score >= thresh) and (len(failing_feedbacks) == 0)

                if self.is_holding_correctly:
                    self.active_feedback = ""
                    if self._hold_start is None:
                        self._hold_start = now
                    self.hold_duration_secs = now - self._hold_start
                else:
                    self._hold_start = None
                    self.hold_duration_secs = 0.0
                    self.active_feedback = failing_feedbacks[0] if failing_feedbacks else "Align form with target"

        else:
            # Fallback mode (timed interval for front-facing occluded postures)
            self.alignment_score = 100.0
            self.is_holding_correctly = True
            self.active_feedback = f"Guided Timed Step ({cfg['name']})"
            if self._hold_start is None:
                self._hold_start = now
            self.hold_duration_secs = now - self._hold_start

        # Check for transition to next step
        if self.hold_duration_secs >= target_duration:
            self.advance_step()

        if draw and img is not None:
            self._draw_overlay(img)

    def advance_step(self) -> None:
        if self.step_idx + 1 < len(SURYA_NAMASKAR_STEPS):
            self.step_idx += 1
            self.reset_step_state()
        else:
            self.sequence_completed = True
            self.total_completed_rounds += 1
            self.reset_step_state()

    def _draw_overlay(self, img: np.ndarray) -> None:
        cfg = self.current_step_config
        h, w = img.shape[:2]

        # Draw header box
        cv2.rectangle(img, (0, 0), (w, 55), (20, 20, 20), -1)
        step_str = f"Step {self.step_idx + 1}/12: {cfg['name']}"
        cv2.putText(img, step_str, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR_WHITE, 2)

        # Draw progress & status box at bottom
        box_y = h - 60
        cv2.rectangle(img, (0, box_y), (w, h), (20, 20, 20), -1)

        dur = cfg["duration"]
        pct = min(self.hold_duration_secs / max(dur, 1.0), 1.0)
        bar_w = int((w - 20) * pct)
        color = COLOR_GREEN if self.is_holding_correctly else COLOR_ORANGE

        # Progress bar
        cv2.rectangle(img, (10, h - 20), (10 + bar_w, h - 8), color, -1)
        cv2.rectangle(img, (10, h - 20), (w - 10, h - 8), COLOR_WHITE, 1)

        status_text = f"Hold: {self.hold_duration_secs:.1f}s / {dur:.0f}s"
        if self.active_feedback:
            status_text += f" - {self.active_feedback}"

        cv2.putText(img, status_text[:65], (15, h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_WHITE, 1)
