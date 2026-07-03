# ============================================================
#  setup_mode.py  –  Camera placement guide & auto-detect
# ============================================================
#  CameraSetup  : checks that all body parts are visible
#                 before allowing the workout to start.
#  AutoDetector : looks at joint angles each frame and
#                 guesses which exercise the user is doing.
# ============================================================

import time
import cv2
from collections import deque
from config import (
    SETUP_LANDMARKS, SETUP_VISIBILITY_THRESHOLD,
    SETUP_HOLD_SECONDS, EXERCISE_CONFIG,
    FRAME_WIDTH, FRAME_HEIGHT,
    COLOR_GREEN, COLOR_RED, COLOR_WHITE,
    COLOR_CYAN, COLOR_ORANGE,
)


# ── Helper ────────────────────────────────────────────────────
def draw_rect_alpha(img, pt1, pt2, color, alpha=0.5):
    overlay = img.copy()
    cv2.rectangle(overlay, pt1, pt2, color, cv2.FILLED)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


# ═══════════════════════════════════════════════════════════════
class CameraSetup:
    """
    Runs a setup phase that checks full-body visibility.

    Call check(results) once per frame; it returns True once the
    user has been fully visible for SETUP_HOLD_SECONDS seconds.
    """

    def __init__(self):
        self._hold_start : float | None = None   # when continuous visibility began
        self._history = deque(maxlen=5)

    # ── Main check ──────────────────────────────────────────
    def check(self, results) -> bool:
        """
        Parameters
        ----------
        results : mediapipe pose results object

        Returns
        -------
        True  -> full body visible long enough; exit setup mode
        False -> still waiting
        """
        visibility = self._check_landmarks(results)
        all_ok     = all(visibility.values())
        self._history.append(all_ok)

        ok_count = sum(self._history)
        total_count = len(self._history)

        # Allow up to 1 bad frame in a rolling window of 5 frames
        if total_count >= 5:
            sufficient = (ok_count >= 4)
        else:
            sufficient = (ok_count == total_count)

        if sufficient:
            if self._hold_start is None:
                self._hold_start = time.time()
            elapsed = time.time() - self._hold_start
            if elapsed >= SETUP_HOLD_SECONDS:
                return True          # ready to start!
        else:
            self._hold_start = None  # reset timer if too many bad frames

        return False

    def draw_overlay(self, img, results):
        """Render the setup checklist and guidance text."""
        visibility = self._check_landmarks(results)

        # Dark background panel
        draw_rect_alpha(img, (0, 0), (FRAME_WIDTH, FRAME_HEIGHT),
                        (10, 10, 30), alpha=0.55)

        # Title
        title = "CAMERA SETUP MODE"
        tw = cv2.getTextSize(title, cv2.FONT_HERSHEY_PLAIN, 3, 3)[0][0]
        cv2.putText(img, title, (FRAME_WIDTH // 2 - tw // 2, 70),
                    cv2.FONT_HERSHEY_PLAIN, 3, COLOR_CYAN, 3)
        cv2.line(img, (100, 90), (FRAME_WIDTH - 100, 90), COLOR_CYAN, 2)

        # Checklist
        y = 140
        for part, ok in visibility.items():
            mark  = "OK" if ok else "X"
            color = COLOR_GREEN if ok else COLOR_RED
            cv2.putText(img, f"{part:<12}: {mark}",
                        (FRAME_WIDTH // 2 - 120, y),
                        cv2.FONT_HERSHEY_PLAIN, 2.0, color, 2)
            y += 50

        # Guidance hint (passes results for position-based advice)
        hint = self._guidance_hint(visibility, results)
        if hint:
            hw = cv2.getTextSize(hint, cv2.FONT_HERSHEY_PLAIN, 1.8, 2)[0][0]
            cv2.putText(img, hint,
                        (FRAME_WIDTH // 2 - hw // 2, y + 30),
                        cv2.FONT_HERSHEY_PLAIN, 1.8, COLOR_ORANGE, 2)

        # Progress bar (time held)
        if self._hold_start is not None:
            elapsed = time.time() - self._hold_start
            pct     = min(elapsed / SETUP_HOLD_SECONDS, 1.0)
            bar_w   = 400
            bx      = FRAME_WIDTH // 2 - bar_w // 2
            by      = FRAME_HEIGHT - 80
            cv2.rectangle(img, (bx, by), (bx + bar_w, by + 30), (80, 80, 80), cv2.FILLED)
            cv2.rectangle(img, (bx, by),
                          (bx + int(bar_w * pct), by + 30), COLOR_GREEN, cv2.FILLED)
            cv2.rectangle(img, (bx, by), (bx + bar_w, by + 30), COLOR_WHITE, 2)
            cv2.putText(img, "Hold still…",
                        (bx, by - 10),
                        cv2.FONT_HERSHEY_PLAIN, 1.5, COLOR_WHITE, 2)

    # ── Private helpers ─────────────────────────────────────
    def _check_landmarks(self, results) -> dict:
        """Return {part_name: bool} for each group in SETUP_LANDMARKS."""
        status = {}
        for part, ids in SETUP_LANDMARKS.items():
            if results is None or not results.pose_landmarks:
                status[part] = False
                continue
            lms = results.pose_landmarks.landmark
            status[part] = all(
                lms[i].visibility >= SETUP_VISIBILITY_THRESHOLD
                for i in ids if i < len(lms)
            )
        return status

    def _guidance_hint(self, visibility: dict, results=None) -> str:
        """
        ISSUE 7: Produce specific placement guidance based on which
        landmarks are missing and, when possible, their estimated
        positions relative to the frame.
        """
        has_upper = visibility.get("Head") and visibility.get("Shoulders")
        has_lower = visibility.get("Knees") and visibility.get("Ankles")
        has_mid   = visibility.get("Hips")

        # Both upper and lower missing → probably too close
        if not has_upper and not has_lower:
            return "Step back – move 1-2 meters from camera"

        # Lower body missing → camera too high or user too close
        if not has_lower:
            if has_upper and has_mid:
                return "Step back or lower the camera slightly"
            return "Lower body not visible – move back 1-2 meters"

        # Upper body missing → camera too low or user too far
        if not has_upper:
            return "Upper body missing – raise the camera"

        # Hips missing but legs/head visible → user not centred
        if not has_mid:
            return "Center yourself in frame"

        if all(visibility.values()):
            return "Great! Hold still to start…"

        return "Adjust your position so your full body is visible"


# ═══════════════════════════════════════════════════════════════
class AutoDetector:
    """
    ISSUE 6: Improved exercise auto-detector using a multi-factor
    scoring system instead of simple if/elif voting.

    Each frame computes a confidence score for every exercise using:
      - knee angle  (squat indicator)
      - elbow angle (curl/pushup indicator)
      - hip angle   (torso orientation: upright vs horizontal)
      - torso tilt  (shoulder-hip vertical alignment)

    Scores are accumulated over a rolling window, then the exercise
    with the highest cumulative score wins.
    """

    _HISTORY = 45   # frames per detection window (~1.5 s at 30 fps)

    def __init__(self):
        self.exercise  : str  = "squats"
        # Accumulate float scores per exercise each window
        self._scores   : dict = {k: 0.0 for k in EXERCISE_CONFIG}
        self._frame    : int  = 0

    def update(self, lm_list: list, detector) -> str:
        """
        Parameters
        ----------
        lm_list  : landmark list from PoseDetector.find_position()
        detector : PoseDetector instance (for find_angle, lm_list)

        Returns
        -------
        Current best-guess exercise key string.
        """
        if not lm_list or len(lm_list) < 29:
            return self.exercise

        self._frame += 1

        # ── Sample joint angles ──────────────────────────────
        knee_l  = detector.find_angle(None, 23, 25, 27, draw=False)
        knee_r  = detector.find_angle(None, 24, 26, 28, draw=False)
        knee    = (knee_l + knee_r) / 2.0

        elbow_l = detector.find_angle(None, 11, 13, 15, draw=False)
        elbow_r = detector.find_angle(None, 12, 14, 16, draw=False)
        elbow   = (elbow_l + elbow_r) / 2.0

        # Hip angle = shoulder-hip-knee (torso inclination)
        hip_l   = detector.find_angle(None, 11, 23, 25, draw=False)
        hip_r   = detector.find_angle(None, 12, 24, 26, draw=False)
        hip     = (hip_l + hip_r) / 2.0

        # Torso tilt: vertical distance between shoulder mid and hip mid
        # Positive = upright; negative/small = leaning forward (pushup)
        sh_y  = (lm_list[11][2] + lm_list[12][2]) / 2.0
        hip_y = (lm_list[23][2] + lm_list[24][2]) / 2.0
        kn_y  = (lm_list[25][2] + lm_list[26][2]) / 2.0
        # Normalise torso length so distance is scale-independent
        torso_len = max(abs(hip_y - sh_y), 1)
        # How far knees are below hips relative to torso (0=standing, +ve=squatting)
        knee_drop = (kn_y - hip_y) / torso_len

        # ── Per-exercise scoring ─────────────────────────────
        # Each condition contributes a weighted confidence point.

        squat_score = 0.0
        # Knees bending in squat range
        if 150 < knee < 230:
            squat_score += 3.0
        # Torso upright (hip angle large)
        if hip > 140:
            squat_score += 2.0
        # Knees visibly below hips (user crouching)
        if knee_drop > 0.3:
            squat_score += 2.0

        pushup_score = 0.0
        # Elbows bending
        if 180 < elbow < 290:
            pushup_score += 3.0
        # Torso inclined / horizontal (hip angle small)
        if hip < 130:
            pushup_score += 3.0
        # Knees roughly level with hips (lying flat)
        if abs(knee_drop) < 0.2:
            pushup_score += 2.0

        curl_score = 0.0
        # Elbow flexion similar to pushups but...
        if 180 < elbow < 290:
            curl_score += 2.0
        # ...torso is upright (not leaning like pushup)
        if hip > 140:
            curl_score += 3.0
        # Knees straight (standing)
        if knee > 155:
            curl_score += 2.0

        self._scores["squats"]  += squat_score
        self._scores["pushups"] += pushup_score
        self._scores["curls"]   += curl_score

        # Every _HISTORY frames: pick winner, reset
        if self._frame >= self._HISTORY:
            self.exercise = max(self._scores, key=lambda k: float(self._scores[k]))
            self._scores  = {k: 0.0 for k in EXERCISE_CONFIG}
            self._frame   = 0

        return self.exercise
