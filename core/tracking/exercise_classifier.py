# ================================================================
#  exercise_classifier.py  –  Automatic exercise recognition
# ================================================================
#  ExerciseClassifier uses a sliding window of pose angle signals
#  to score each exercise and select the most likely one.
#
#  Signals used per frame:
#    knee_flex        – average knee angle  (low = squatting)
#    elbow_flex       – average elbow angle (low = bending arm)
#    hip_angle        – torso inclination   (low = leaning forward)
#    arms_overhead    – wrist y vs shoulder y (negative = arms up)
#    torso_horizontal – shoulder y ≈ hip y (lying flat)
#    torso_upright    – large shoulder→hip→knee angle
#    split_stance     – left vs right knee height differ a lot
#
#  Each exercise defines which signals it scores highly on.
#  Scores accumulate over a WINDOW_FRAMES window, then the winner
#  is selected.
# ================================================================

import numpy as np
from core.utils.config import EXERCISE_CONFIG, FRAME_HEIGHT, CLASSIFIER_SWITCH_MARGIN


# Per-exercise signal weights  { exercise_key: { signal: weight } }
_SIGNAL_WEIGHTS = {
    "squats": {
        "knee_flex"    : 3.0,
        "hip_upright"  : 2.0,
        "torso_upright": 1.5,
    },
    "pushups": {
        "elbow_flex"       : 3.0,
        "torso_horizontal" : 3.0,
    },
    "curls": {
        "elbow_flex"   : 3.0,
        "torso_upright": 2.0,
        "hip_upright"  : 1.5,
    },
    "lunges": {
        "knee_flex"    : 2.5,
        "split_stance" : 3.0,
        "torso_upright": 1.5,
    },
    "shoulder_press": {
        "elbow_flex"    : 2.5,
        "arms_overhead" : 3.5,
        "torso_upright" : 1.0,
    },
}

WINDOW_FRAMES = 90   # frames per classification window (~3 s at 30 fps)


class ExerciseClassifier:
    """
    Automatic exercise classifier.

    Usage
    -----
        clf = ExerciseClassifier()
        exercise_key = clf.update(lm_list, detector)
    """

    def __init__(self):
        self.exercise : str   = "squats"   # current best guess
        self._scores  : dict  = {k: 0.0 for k in EXERCISE_CONFIG}
        self._frame   : int   = 0
        
        self._pending_candidate: str | None = None
        self._pending_count: int = 0

        # Smoothed signal values for the debug readout
        self._signals : dict  = {}

    def update(self, lm_list: list, detector) -> str:
        """
        Parameters
        ----------
        lm_list  : output of PoseDetector.find_position()
        detector : PoseDetector instance (used for find_angle)

        Returns
        -------
        Best-guess exercise key string.
        """
        if not lm_list or len(lm_list) < 29:
            return self.exercise

        self._frame += 1
        signals = self._compute_signals(lm_list, detector)
        self._signals = signals   # expose for debug

        # Accumulate scores
        for ex_key, weights in _SIGNAL_WEIGHTS.items():
            frame_score = 0.0
            for sig_name, weight in weights.items():
                frame_score += signals.get(sig_name, 0.0) * weight
            self._scores[ex_key] += frame_score

        # Every window: pick winner and reset
        if self._frame >= WINDOW_FRAMES:
            candidate = max(self._scores, key=lambda k: float(self._scores[k]))
            current_score = float(self._scores.get(self.exercise, 0.0))
            candidate_score = float(self._scores[candidate])

            if candidate != self.exercise and candidate_score > current_score * CLASSIFIER_SWITCH_MARGIN:
                if candidate == self._pending_candidate:
                    self._pending_count += 1
                else:
                    self._pending_candidate = candidate
                    self._pending_count = 1

                if self._pending_count >= 2:
                    self.exercise = candidate
                    self._pending_candidate = None
                    self._pending_count = 0
            else:
                self._pending_candidate = None
                self._pending_count = 0

            self._scores  = {k: 0.0 for k in EXERCISE_CONFIG}
            self._frame   = 0

        return self.exercise

    # ── Signal computation ────────────────────────────────────
    def _compute_signals(self, lm_list: list, detector) -> dict:
        """
        Compute normalised [0, 1] signal values from pose landmarks.
        1.0 = signal strongly present, 0.0 = not present.
        """
        signals = {}

        # ── Knee flex: both knees bending ────────────────────
        kl = detector.find_angle(None, 23, 25, 27, draw=False)
        kr = detector.find_angle(None, 24, 26, 28, draw=False)
        knee_avg = (kl + kr) / 2.0
        # Deep knee bend: angle ≈ 90°.  Standing: ≈ 170°.
        # Signal is strong (1.0) when knee_avg ≈ 90-120, weak at >160
        signals["knee_flex"] = float(np.clip(
            np.interp(knee_avg, (90, 170), (1.0, 0.0)), 0, 1))

        # ── Elbow flex ────────────────────────────────────────
        el = detector.find_angle(None, 11, 13, 15, draw=False)
        er = detector.find_angle(None, 12, 14, 16, draw=False)
        elbow_avg = (el + er) / 2.0
        signals["elbow_flex"] = float(np.clip(
            np.interp(elbow_avg, (60, 170), (1.0, 0.0)), 0, 1))

        # ── Hip angle (torso inclination) ─────────────────────
        # Angle at hip (shoulder→hip→knee).  Upright ≈ 170-180°.
        hl = detector.find_angle(None, 11, 23, 25, draw=False)
        hr = detector.find_angle(None, 12, 24, 26, draw=False)
        hip_avg = (hl + hr) / 2.0
        signals["hip_upright"] = float(np.clip(
            np.interp(hip_avg, (100, 175), (0.0, 1.0)), 0, 1))

        # ── Torso horizontal (pushup lying flat) ─────────────
        sh_y  = (lm_list[11][2] + lm_list[12][2]) / 2.0
        hip_y = (lm_list[23][2] + lm_list[24][2]) / 2.0
        frame_h = FRAME_HEIGHT   # configured frame height
        vert_diff = abs(sh_y - hip_y) / frame_h  # 0=same height, 1=very different
        signals["torso_horizontal"] = float(np.clip(
            np.interp(vert_diff, (0.0, 0.15), (1.0, 0.0)), 0, 1))

        # ── Torso upright (standing exercises) ───────────────
        signals["torso_upright"] = 1.0 - signals["torso_horizontal"]

        # ── Arms overhead ────────────────────────────────────
        # Wrist y < shoulder y in image space (y increases downward)
        # → arms are above head
        wl_y  = lm_list[15][2]   # left  wrist
        wr_y  = lm_list[16][2]   # right wrist
        shl_y = lm_list[11][2]   # left  shoulder
        shr_y = lm_list[12][2]   # right shoulder
        # Positive when wrists are ABOVE shoulders (y smaller)
        overhead_l = (shl_y - wl_y) / max(frame_h, 1)
        overhead_r = (shr_y - wr_y) / max(frame_h, 1)
        overhead   = (overhead_l + overhead_r) / 2.0
        signals["arms_overhead"] = float(np.clip(overhead * 5.0, 0, 1))

        # ── Split stance (lunges) ─────────────────────────────
        # Left and right knees are at very different heights
        kl_y = lm_list[25][2]
        kr_y = lm_list[26][2]
        knee_height_diff = abs(kl_y - kr_y) / max(frame_h, 1)
        signals["split_stance"] = float(np.clip(
            np.interp(knee_height_diff, (0.05, 0.25), (0.0, 1.0)), 0, 1))

        return signals
