# ================================================================
#  frame_pipeline.py  –  Shared per-frame processing pipeline
# ================================================================

import os
import cv2
import time
import skops.io as sio
import numpy as np
import logging
from typing import cast

from core.utils.config import (
    COLOR_GREEN, COLOR_RED, COLOR_ORANGE, EXERCISE_CONFIG, MODEL_SKOPS_PATH,
    FRAME_WIDTH, FRAME_HEIGHT, CLEAN_REP_SCORE_THRESHOLD,
)
from core.tracking.pose_module import PoseDetector
from core.tracking.exercises import ExerciseTracker
from core.tracking.exercise_classifier import ExerciseClassifier
from core.data.session_tracker import WorkoutSession
from core.tracking.setup_mode import CameraSetup
from core.utils.voice_coach import VoiceCoach


from core.utils.utils import (
    draw_progress_bar, draw_rep_panel, draw_stats_panel,
    draw_exercise_badge, draw_fps, draw_feedback,
    draw_hints, draw_symmetry_panel, draw_form_score,
    draw_stage_indicator, draw_debug_overlay,
    draw_rep_quality_flash,
)

logger = logging.getLogger("frame_pipeline")


def _load_ml_model():
    if os.path.isfile(MODEL_SKOPS_PATH):
        try:
            untrusted = sio.get_untrusted_types(file=MODEL_SKOPS_PATH)
            model = sio.load(MODEL_SKOPS_PATH, trusted=untrusted) if not untrusted else None
            if model is not None:
                logger.info(f"ML model loaded from {MODEL_SKOPS_PATH}")
            return model
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}")
    return None


def _ml_score(model, tracker: ExerciseTracker) -> float:
    if model is None:
        return -1.0
    rows = tracker.get_feature_rows()
    if not rows:
        return -1.0
    last = rows[-1]
    features = np.array([[
        last["symmetry"],
        last["range_of_motion"],
        last["posture"],
        last["control"],
    ]])
    try:
        prob = model.predict_proba(features)[0][1]   # P(good_rep)
        return float(prob * 100.0)
    except Exception:
        return -1.0


def _blended_score(rule_score: float, ml_score: float) -> float:
    if ml_score < 0:
        return rule_score
    return 0.6 * rule_score + 0.4 * ml_score


class FramePipeline:
    """
    Shared per-frame processing pipeline used by both the desktop
    OpenCV entry point (main.py) and the browser WebRTC entry point
    (live_app.py). Owns no camera or window state - only receives a
    frame and returns a processed frame plus the current tracker state.
    
    Parameters
    ----------
    video_mode : bool
        If True, uses MediaPipe VIDEO running mode (temporal tracking
        across frames) which dramatically improves detection on
        recorded videos.  Use False for live WebRTC streams.
    """

    def __init__(self, exercise_key: str = "squats", in_setup: bool = True,
                 video_mode: bool = False):
        self.detector    = PoseDetector(video_mode=video_mode)
        self.setup       = CameraSetup()
        self.classifier  = ExerciseClassifier()
        self.session     = WorkoutSession()
        self.voice       = VoiceCoach()
        self.ml_model    = _load_ml_model()
        self.video_mode  = video_mode
        self._frame_idx  = 0   # used to compute timestamps for VIDEO mode

        self.current_key = exercise_key
        self.tracker      = ExerciseTracker(exercise_key)
        self.auto_mode    = False
        self.show_debug   = False
        self.in_setup     = in_setup

        # Timing & State
        self.prev_time      = time.time()
        self.fps            = 0.0
        self.flash_frames   = 0
        self.FLASH_DURATION = 45

        self.prev_rep_count   = 0
        self.inserted_rep_ids: list[int] = []

        # Voice output suppression & text overlay captions
        self.voice_muted      = False
        self.is_browser       = False
        self.coaching_caption: str | None = None
        self.caption_expiry   = 0.0

        self.session.start()

    def set_exercise(self, exercise_key: str) -> None:
        """Called by either UI (keyboard handler or Streamlit sidebar button)."""
        logger.info(f"Switching exercise to: {exercise_key}")
        self.current_key = exercise_key
        self.tracker     = ExerciseTracker(exercise_key)
        self.prev_rep_count = 0
        self.flash_frames   = 0

    def toggle_auto_mode(self) -> None:
        self.auto_mode = not self.auto_mode
        logger.info(f"Auto-detect {'ON' if self.auto_mode else 'OFF'}")
        if not self.voice_muted:
            self.voice.say(f"Auto detect {'on' if self.auto_mode else 'off'}", is_browser=self.is_browser)
        else:
            self.set_coaching_caption(f"Auto detect {'on' if self.auto_mode else 'off'}")

    def set_coaching_caption(self, phrase: str) -> None:
        self.coaching_caption = phrase
        self.caption_expiry   = time.time() + 3.0  # display for 3.0 seconds

    @staticmethod
    def _letterbox(img: np.ndarray, target_w: int = FRAME_WIDTH,
                   target_h: int = FRAME_HEIGHT) -> np.ndarray:
        """Pad *img* to target aspect ratio with black bars, then resize.
        Preserves the original aspect ratio so landmark geometry is correct."""
        h, w = img.shape[:2]
        target_ratio = target_w / target_h
        src_ratio    = w / h

        if abs(src_ratio - target_ratio) < 0.01:   # already 16:9
            return cv2.resize(img, (target_w, target_h))

        if src_ratio > target_ratio:               # wider than 16:9 → pillarbox
            new_w = target_w
            new_h = int(target_w / src_ratio)
        else:                                       # taller than 16:9 → letterbox
            new_h = target_h
            new_w = int(target_h * src_ratio)

        resized = cv2.resize(img, (new_w, new_h))
        canvas  = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        y_off   = (target_h - new_h) // 2
        x_off   = (target_w - new_w) // 2
        canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
        return canvas

    def process_frame(self, img: np.ndarray, src_fps: float = 30.0) -> np.ndarray:
        """
        Run one frame through pose detection, exercise tracking, and
        overlay drawing. Returns the annotated image.
        
        Parameters
        ----------
        img     : Raw BGR frame from camera or video file.
        src_fps : Source video FPS (used to compute VIDEO-mode timestamps).
        """
        # Letterbox to target resolution — preserves aspect ratio.
        img = self._letterbox(img)

        self._frame_idx += 1
        timestamp_ms = int(self._frame_idx * 1000 / max(src_fps, 1.0))

        # ── Pose detection ────────────────────────────────────
        img     = self.detector.find_pose(img, draw=False, timestamp_ms=timestamp_ms)
        lm_list = self.detector.find_position(img, draw=False)

        # ════════════════════════════════════════════════════════
        # PHASE 1 – Camera setup
        # ════════════════════════════════════════════════════════
        if self.in_setup:
            self.setup.draw_overlay(img, self.detector.results)
            if self.setup.check(self.detector.results):
                self.in_setup = False
                msg = "Setup complete. Let's train!"
                if not self.voice_muted:
                    self.voice.say(msg, is_browser=self.is_browser)
                self.set_coaching_caption(msg)
                logger.info("Setup complete – workout started.")

            # Under setup, we still draw progress/stats as background context
            # but returning early similar to main.py
            return img

        # ════════════════════════════════════════════════════════
        # PHASE 2 – Workout
        # ════════════════════════════════════════════════════════

        # ── Auto-detect exercise ──────────────────────────────
        if self.auto_mode and lm_list:
            detected = self.classifier.update(lm_list, self.detector)
            if detected != self.current_key:
                logger.info(f"Auto-detected: {EXERCISE_CONFIG[detected]['display_name']}")
                self.set_exercise(detected)

        cfg = EXERCISE_CONFIG[self.current_key]

        # ── Run exercise tracker ──────────────────────────────
        if lm_list:
            current_time = timestamp_ms / 1000.0 if self.video_mode else None
            self.tracker.update(self.detector, img, lm_list, draw=True, current_time=current_time)
        else:
            self.tracker.feedback      = "No pose detected"
            self.tracker.low_visibility = True

        # ── Detect newly completed reps ───────────────────────
        if self.tracker.total_reps > self.prev_rep_count:
            self.prev_rep_count = self.tracker.total_reps
            self.flash_frames   = self.FLASH_DURATION

            # ML score blending
            ml_s  = _ml_score(self.ml_model, self.tracker)
            final = _blended_score(self.tracker.rep_score, ml_s)

            # Session recording
            self.session.record_rep(
                exercise_key = self.current_key,
                rep_score    = final,
                calories     = cast(float, cfg["kcal_per_rep"]),
                is_clean     = self.tracker.last_rep_was_clean,
            )

            # Dynamic accumulation
            new_rows = self.tracker.get_feature_rows()
            if new_rows:
                last_row = new_rows[-1]
                last_row["rep_score"] = round(final, 2)
                last_row["rep_label"] = "good_rep" if final >= CLEAN_REP_SCORE_THRESHOLD else "bad_rep"
                self.session.add_feature_row(last_row)
                
                # Rep is incrementally saved to DB synchronously inside session.add_feature_row().

            # Voice coaching / Captions
            rom_ok = self.tracker.last_rep_min_angle <= cast(float, cfg.get("rom_min_angle", 100.0))
            vel_hi = any(v < 60 for v in self.tracker.last_rep_velocity_samples[-5:]) \
                     if self.tracker.last_rep_velocity_samples else False
            
            phrase = self.voice._select_phrase(
                self.current_key, final,
                self.tracker.is_asymmetric, self.tracker.bad_posture,
                rom_ok, vel_hi,
            )
            if phrase:
                if not self.voice_muted:
                    self.voice.say(phrase, is_browser=self.is_browser)
                self.set_coaching_caption(phrase)

        # ── Low Visibility Coaching ───────────────────────────
        if self.tracker.low_visibility and self.tracker.feedback and self.tracker.feedback != "No pose detected":
            if not self.voice_muted:
                self.voice.say(self.tracker.feedback + ", step back", is_browser=self.is_browser)
            self.set_coaching_caption(self.tracker.feedback)

        # ── FPS ───────────────────────────────────────────────
        now            = time.time()
        self.fps       = 1.0 / max(now - self.prev_time, 1e-6)
        self.prev_time = now

        # ── Bar colour ────────────────────────────────────────
        bar_color = COLOR_GREEN if self.tracker.percentage >= 90 else COLOR_RED

        # ── Feedback colour ───────────────────────────────────
        if self.tracker.low_visibility or self.tracker.bad_posture or self.tracker.is_asymmetric:
            fb_color = COLOR_RED
        elif self.tracker.feedback == cfg["feedback_good"]:
            fb_color = COLOR_GREEN
        else:
            fb_color = COLOR_ORANGE

        # Overwrite visible feedback with coaching caption if active
        feedback_text = self.tracker.feedback
        if self.coaching_caption and time.time() < self.caption_expiry:
            feedback_text = self.coaching_caption

        # ── Draw UI ───────────────────────────────────────────
        draw_exercise_badge(img, cast(str, cfg["display_name"]), self.auto_mode)
        draw_progress_bar(  img, self.tracker.percentage, bar_color)
        draw_rep_panel(     img, self.tracker.total_reps,
                            self.tracker.clean_reps, self.tracker.bad_reps,
                            self.tracker.rep_score)
        draw_stats_panel(   img, self.session.total_calories,
                            self.session.elapsed, self.session.reps_per_minute)
        draw_symmetry_panel(img, self.tracker.symmetry_score, self.tracker.is_asymmetric)
        draw_form_score(    img, self.tracker.form_score)
        draw_stage_indicator(img, self.tracker.stage)
        draw_feedback(      img, feedback_text, fb_color)
        draw_hints(         img, self.auto_mode)
        draw_fps(           img, self.fps)

        if self.show_debug:
            draw_debug_overlay(img, {
                "left_angle"   : self.tracker.left_angle,
                "right_angle"  : self.tracker.right_angle,
                "avg_angle"    : self.tracker.avg_angle,
                "posture_angle": self.tracker.posture_angle,
                "velocity"     : self.tracker.velocity,
                "stage"        : self.tracker.stage,
            })

        if self.flash_frames > 0:
            draw_rep_quality_flash(img, self.tracker.rep_score)
            self.flash_frames -= 1

        return img

    def get_summary(self) -> dict:
        """Returns session.summary() plus tracker averages, for end-of-session display."""
        s = self.session.summary()
        s["avg_symmetry"] = self.tracker.avg_symmetry
        s["avg_form"] = self.tracker.avg_form
        return s
