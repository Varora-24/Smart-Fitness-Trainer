# ================================================================
#  exercises.py  –  Exercise tracking logic  v3 Pro
# ================================================================
#  Architecture
#  ─────────────────────────────────────────────────────────────
#  ExerciseTracker
#    • Multi-joint validation (primary + posture chain)
#    • Explicit UP/DOWN stage state machine
#    • ROM min/max tracking with configurable thresholds
#    • MediaPipe landmark visibility gate
#    • Angle smoothing via AngleSmoother (from utils)
#    • Velocity / jerk detection
#    • Rep quality score (0-100) per rep
#    • CSV feature export hook for ML training
#    • Supports all 5 exercises via config.py
# ================================================================

import time
from typing import Any
import numpy as np
from config import (
    EXERCISE_CONFIG,
    LANDMARK_VISIBILITY_THRESHOLD,
    FEEDBACK_DEPTH_THRESHOLD,
    SYMMETRY_WARN_TEXT,
    VISIBILITY_WARN_TEXT,
    FORM_WEIGHT_SYMMETRY,
    FORM_WEIGHT_ROM,
    FORM_WEIGHT_POSTURE,
    FORM_WEIGHT_CONTROL,
    CLEAN_REP_SCORE_THRESHOLD,
    MAX_VELOCITY_DEG_PER_FRAME,
)
from utils import AngleSmoother


class ExerciseTracker:
    """
    Full-featured bilateral exercise tracker supporting all 5 exercises.

    Parameters
    ----------
    exercise_key : one of "squats" | "pushups" | "curls" |
                          "lunges" | "shoulder_press"
    """

    def __init__(self, exercise_key: str):
        if exercise_key not in EXERCISE_CONFIG:
            raise ValueError(
                f"Unknown exercise '{exercise_key}'. "
                f"Valid: {list(EXERCISE_CONFIG.keys())}"
            )

        self.key = exercise_key
        self.cfg: dict[str, Any] = EXERCISE_CONFIG[exercise_key]

        # ── Counters ─────────────────────────────────────────
        self.total_reps  : int   = 0
        self.clean_reps  : int   = 0
        self.bad_reps    : int   = 0
        self.calories    : float = 0.0

        # ── State machine ────────────────────────────────────
        # stage: "up" = at start position, "down" = reached bottom
        self.stage       : str   = "up"

        # ── Smoothers (one per side, one per posture chain) ──
        self._sm_left    = AngleSmoother()
        self._sm_right   = AngleSmoother()
        self._sm_post_l  = AngleSmoother()
        self._sm_post_r  = AngleSmoother()

        # ── Per-rep accumulators ─────────────────────────────
        self._rep_min_angle   : float = 360.0   # smallest primary angle seen
        self._rep_max_angle   : float = 0.0     # largest primary angle seen
        self._sym_samples     : list  = []
        self._posture_samples : list  = []
        self._velocity_samples: list  = []
        self._prev_avg_angle  : float = 0.0
        self._rep_start_time  : float = time.time()

        # ── Session accumulators ─────────────────────────────
        self._all_rep_scores  : list  = []
        self._all_sym_scores  : list  = []
        self._all_form_scores : list  = []
        # Feature rows for ML dataset export
        self._feature_rows    : list  = []

        # ── Public frame-state ───────────────────────────────
        self.percentage      : float = 0.0
        self.left_angle      : float = 0.0
        self.right_angle     : float = 0.0
        self.avg_angle       : float = 0.0
        self.posture_angle   : float = 0.0     # secondary validation angle
        self.symmetry_score  : float = 100.0
        self.form_score      : float = 100.0
        self.rep_score       : float = 0.0     # score of most recent rep
        self.velocity        : float = 0.0     # |angle change| this frame
        self.feedback        : str   = ""
        self.is_asymmetric   : bool  = False
        self.bad_posture     : bool  = False
        self.low_visibility  : bool  = False
        # Flash flag: set True for one frame after a rep completes
        self.rep_just_finished: bool = False

        # ── Last rep stats ───────────────────────────────────
        self.last_rep_min_angle      : float = 360.0
        self.last_rep_velocity_samples: list  = []
        self.last_rep_rom_score      : float = 0.0
        self.last_rep_control_score  : float = 0.0
        self.last_rep_was_clean      : bool  = False
        self.last_rep_time   : float = 0.0   # for inter-rep debounce
        self._posture_baseline       : float | None = None

    # ── Public properties ────────────────────────────────────
    @property
    def reps(self) -> int:
        """Alias for total_reps (backward-compatible)."""
        return self.total_reps

    @property
    def avg_symmetry(self) -> float:
        return round(float(np.mean(self._all_sym_scores)), 1) \
               if self._all_sym_scores else 100.0

    @property
    def avg_form(self) -> float:
        return round(float(np.mean(self._all_form_scores)), 1) \
               if self._all_form_scores else 0.0

    @property
    def avg_rep_score(self) -> float:
        return round(float(np.mean(self._all_rep_scores)), 1) \
               if self._all_rep_scores else 0.0

    # ── Main update (one call per camera frame) ───────────────
    def update(
        self,
        detector,           # PoseDetector instance
        img,                # current BGR frame (for drawing)
        lm_list : list,     # landmark list from detector.find_position()
        draw    : bool = True,
    ) -> None:
        """
        Process one frame.  Reads angles directly from the detector
        so it can validate both primary and posture joint chains.
        """
        self.rep_just_finished = False
        self.bad_posture = False
        cfg = self.cfg

        # ── 1. Visibility gate ────────────────────────────────
        self.low_visibility = not self._check_visibility(detector)
        if self.low_visibility:
            self.feedback = VISIBILITY_WARN_TEXT
            return

        # ── 2. Compute primary angles (both sides) ────────────
        lL, lR = cfg["landmarks_left"], cfg["landmarks_right"]
        if max(*lL, *lR) >= len(lm_list):
            self.feedback = "Move into frame"
            return

        raw_left  = detector.find_angle(img, lL[0], lL[1], lL[2], draw=draw)
        raw_right = detector.find_angle(img, lR[0], lR[1], lR[2], draw=draw)

        self.left_angle  = self._sm_left.update(raw_left)
        self.right_angle = self._sm_right.update(raw_right)
        self.avg_angle   = (self.left_angle + self.right_angle) / 2.0

        # ── 3. Velocity ───────────────────────────────────────
        self.velocity = abs(self.avg_angle - self._prev_avg_angle)
        self._prev_avg_angle = self.avg_angle

        # ── 4. Posture chain validation ───────────────────────
        pL, pR = cfg["posture_chain_left"], cfg["posture_chain_right"]
        post_ok = True
        if max(*pL, *pR) < len(lm_list):
            pl_raw = detector.find_angle(img, pL[0], pL[1], pL[2], draw=False)
            pr_raw = detector.find_angle(img, pR[0], pR[1], pR[2], draw=False)
            pl = self._sm_post_l.update(pl_raw)
            pr = self._sm_post_r.update(pr_raw)
            self.posture_angle = (pl + pr) / 2.0
            
            if self.key == "curls":
                if self._posture_baseline is None:
                    self._posture_baseline = self.posture_angle
                delta = abs(self.posture_angle - self._posture_baseline)
                post_ok = delta <= cfg.get("posture_delta_threshold", 20.0)
            else:
                post_ok = (cfg["posture_min_angle"]
                           <= self.posture_angle
                           <= cfg["posture_max_angle"])
        if not post_ok:
            self.bad_posture = True

        # ── 5. Symmetry ───────────────────────────────────────
        diff = abs(self.left_angle - self.right_angle)
        self.symmetry_score = float(np.clip(100.0 - diff * 2.0, 0, 100))
        self.is_asymmetric  = diff > cfg["symmetry_threshold"]

        # ── 6. Depth percentage (0=start, 100=full depth) ─────
        a_min, a_max = cfg["angle_range"]
        if cfg.get("depth_direction", "down") == "down":
            self.percentage = float(np.clip(
                np.interp(self.avg_angle, (a_min, a_max), (100, 0)),
                0, 100,
            ))
        else:
            self.percentage = float(np.clip(
                np.interp(self.avg_angle, (a_min, a_max), (0, 100)),
                0, 100,
            ))
        # Note: interp(a_min→100, a_max→0) so smaller angle = deeper

        # ── 7. Accumulate per-rep stats ───────────────────────
        self._rep_min_angle = min(self._rep_min_angle, self.avg_angle)
        self._rep_max_angle = max(self._rep_max_angle, self.avg_angle)
        self._sym_samples.append(self.symmetry_score)
        self._posture_samples.append(100.0 if post_ok else 0.0)
        if self.velocity <= MAX_VELOCITY_DEG_PER_FRAME:
            self._velocity_samples.append(100.0)
        else:
            # Penalise proportionally to how far over the limit we are
            over = self.velocity - MAX_VELOCITY_DEG_PER_FRAME
            penalty = min(over * 2.0, 80.0)
            self._velocity_samples.append(max(20.0, 100.0 - penalty))

        # ── 8. Live form score ────────────────────────────────
        sym_s = self.symmetry_score
        post_s = 100.0 if post_ok else 30.0
        vel_s = self._velocity_samples[-1]
        rom_s = self.percentage  # live depth as proxy for ROM
        self.form_score = float(np.clip(
            FORM_WEIGHT_SYMMETRY * sym_s
            + FORM_WEIGHT_ROM     * rom_s
            + FORM_WEIGHT_POSTURE * post_s
            + FORM_WEIGHT_CONTROL * vel_s,
            0, 100,
        ))

        # ── 9. Coaching feedback ──────────────────────────────
        if self.bad_posture:
            self.feedback = cfg["feedback_posture"]
        elif self.is_asymmetric:
            self.feedback = SYMMETRY_WARN_TEXT
        elif self.percentage < FEEDBACK_DEPTH_THRESHOLD:
            self.feedback = cfg["feedback_low"]
        else:
            self.feedback = cfg["feedback_good"]

        # ── 10. Stage machine → rep counting ─────────────────
        # Hysteresis: require angle to cross DOWN threshold to start a rep,
        # then cross UP threshold to complete it. The gap between thresholds
        # prevents oscillation-induced false reps.
        if self.avg_angle < cfg.get("stage_down_threshold", 90):
            if self.stage == "up":
                self.stage = "down"
                self._rep_min_angle = self.avg_angle
        elif self.avg_angle > cfg.get("stage_up_threshold", 160):
            if self.stage == "down":
                self.stage = "up"

                # Debounce: at least 0.8 seconds between reps to avoid
                # double-counting fast jitter or oscillation at the threshold.
                current_time = time.time()
                if current_time - self.last_rep_time > 0.8:
                    self.last_rep_time = current_time
                    self._finish_rep()   # _finish_rep() handles total_reps += 1

    # ── Private helpers ───────────────────────────────────────

    def _check_visibility(self, detector) -> bool:
        """
        Return True only when all required landmarks have
        MediaPipe visibility scores above the threshold.
        """
        if detector.results is None:
            return False
        if not detector.results.pose_landmarks:
            return False
        lms = detector.results.pose_landmarks.landmark
        for idx in self.cfg["required_landmarks"]:
            if idx >= len(lms):
                return False
            if lms[idx].visibility < LANDMARK_VISIBILITY_THRESHOLD:
                return False
        return True

    def _compute_rom_score(self) -> float:
        """
        Score range-of-motion using the actual min/max angles
        reached during this rep vs the configured ROM threshold.
        """
        rom_threshold = self.cfg.get("rom_min_angle", 90)
        # Did the angle go below the ROM threshold? (smaller = deeper)
        if self._rep_min_angle <= rom_threshold:
            return 100.0
        # Partial credit: how close did they get?
        gap = self._rep_min_angle - rom_threshold
        return float(np.clip(100.0 - gap * 2.0, 0, 100))

    def _finish_rep(self) -> None:
        """Called once per completed rep (stage down→up transition)."""
        rep_sym     = float(np.mean(self._sym_samples))   if self._sym_samples   else 100.0
        rep_posture = float(np.mean(self._posture_samples)) if self._posture_samples else 100.0
        rep_control = float(np.mean(self._velocity_samples)) if self._velocity_samples else 100.0
        rep_rom     = self._compute_rom_score()

        # Weighted quality score
        rep_score = float(np.clip(
            FORM_WEIGHT_SYMMETRY * rep_sym
            + FORM_WEIGHT_ROM     * rep_rom
            + FORM_WEIGHT_POSTURE * rep_posture
            + FORM_WEIGHT_CONTROL * rep_control,
            0, 100,
        ))

        self.rep_score = rep_score
        # NOTE: total_reps is incremented here (only here — NOT in update())
        self.total_reps += 1
        self.calories   += self.cfg["kcal_per_rep"]

        if rep_score >= CLEAN_REP_SCORE_THRESHOLD:
            self.clean_reps += 1
        else:
            self.bad_reps += 1

        self.last_rep_min_angle = self._rep_min_angle
        self.last_rep_velocity_samples = self._velocity_samples.copy()
        self.last_rep_rom_score = rep_rom
        self.last_rep_control_score = rep_control
        self.last_rep_was_clean = rep_score >= CLEAN_REP_SCORE_THRESHOLD

        self._all_rep_scores.append(rep_score)
        self._all_sym_scores.append(rep_sym)
        self._all_form_scores.append(rep_score)   # form = rep_score here

        # Save features for ML dataset
        self._feature_rows.append({
            "exercise"       : self.key,
            "symmetry"       : round(rep_sym, 2),
            "range_of_motion": round(rep_rom, 2),
            "posture"        : round(rep_posture, 2),
            "control"        : round(rep_control, 2),
            "rep_score"      : round(rep_score, 2),
            "rep_label"      : "good_rep" if rep_score >= CLEAN_REP_SCORE_THRESHOLD
                               else "bad_rep",
        })

        # Signal the UI to flash the rep score
        self.rep_just_finished = True

        # Reset per-rep accumulators
        self._rep_min_angle    = 360.0
        self._rep_max_angle    = 0.0
        self._sym_samples      = []
        self._posture_samples  = []
        self._velocity_samples = []
        self._posture_baseline = None
        self._rep_start_time   = time.time()

    def get_feature_rows(self) -> list:
        """Return collected feature rows for CSV export."""
        return self._feature_rows.copy()

    def reset(self) -> None:
        """Full reset – used when switching exercise."""
        self.__init__(self.key)  # type: ignore[misc]
