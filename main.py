# ================================================================
#  main.py  –  AI Smart Fitness Trainer v3 Pro  (entry point)
# ================================================================
#
#  HOW TO RUN
#  ----------
#  pip install -r requirements.txt
#  python main.py
#
#  KEYBOARD CONTROLS
#  -----------------
#  S  Squats          P  Push-Ups      C  Curls
#  L  Lunges          H  Shoulder Press
#  A  Toggle auto-detect               D  Toggle debug overlay
#  Q  Quit + summary
#
# ================================================================

import cv2
import time
import os
import pickle
import numpy as np
import argparse
import json
import logging
from logger_setup import setup_logger
import db

from config import (
    WINDOW_TITLE, FRAME_WIDTH, FRAME_HEIGHT,
    COLOR_GREEN, COLOR_RED, COLOR_ORANGE, EXERCISE_CONFIG, MODEL_PKL_PATH,
)
from pose_module         import PoseDetector
from exercises           import ExerciseTracker
from exercise_classifier import ExerciseClassifier
from session_tracker     import WorkoutSession
from setup_mode          import CameraSetup
from voice_coach         import VoiceCoach
from utils import (
    draw_progress_bar, draw_rep_panel, draw_stats_panel,
    draw_exercise_badge, draw_fps, draw_feedback,
    draw_hints, draw_symmetry_panel, draw_form_score,
    draw_stage_indicator, draw_debug_overlay,
    draw_rep_quality_flash, show_summary,
)

logger = logging.getLogger("main")


# ── Try loading the trained ML model ─────────────────────────────
def _load_ml_model():
    if os.path.isfile(MODEL_PKL_PATH):
        try:
            with open(MODEL_PKL_PATH, "rb") as fh:
                model = pickle.load(fh)
            logger.info(f"ML model loaded from {MODEL_PKL_PATH}")
            return model
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}")
    return None


def _ml_score(model, tracker: ExerciseTracker) -> float:
    """
    Run the ML model on the latest rep features and return a
    0-100 quality probability.  Returns -1 if model unavailable.
    """
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


# ── Blended score ─────────────────────────────────────────────────
def _blended_score(rule_score: float, ml_score: float) -> float:
    if ml_score < 0:
        return rule_score
    return 0.6 * rule_score + 0.4 * ml_score


def main():
    parser = argparse.ArgumentParser(description="AI Smart Fitness Trainer")
    parser.add_argument("--source", type=str, default="webcam",
                        help="Video source: 'webcam' or path to a video file")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose debugging logs")
    args = parser.parse_args()

    # ── Logging & DB ────────────────────────────────────────────
    setup_logger(args.verbose)
    logger.info("Starting AI Smart Fitness Trainer...")
    
    try:
        db.init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # ── Camera / Video Source ───────────────────────────────────
    if args.source == "webcam":
        source_val = 0
        in_setup = True
    else:
        source_val = args.source
        in_setup = False
        logger.info(f"Using file source: {args.source}. Skipping camera setup.")

    cap = cv2.VideoCapture(source_val)
    if not cap.isOpened():
        logger.error(f"Cannot open video source: {source_val}")
        return

    if args.source == "webcam":
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    # ── Components ──────────────────────────────────────────────
    detector    = PoseDetector()
    setup       = CameraSetup()
    classifier  = ExerciseClassifier()
    session     = WorkoutSession()
    voice       = VoiceCoach()
    ml_model    = _load_ml_model()

    current_key  = "squats"
    tracker      = ExerciseTracker(current_key)
    auto_mode    = False
    show_debug   = False

    # ── Timing & State ──────────────────────────────────────────
    prev_time      = time.time()
    fps            = 0.0
    flash_frames   = 0
    FLASH_DURATION = 45   # frames (~1.5 s at 30 fps)

    # Track previous rep count to detect new reps
    prev_rep_count = 0
    inserted_rep_ids = []

    logger.info("AI Smart Fitness Trainer running. Use keyboard keys to interact.")
    session.start()

    # ════════════════════════════════════════════════════════════
    while True:
        success, img = cap.read()
        if not success:
            logger.warning("Frame read failed – retrying…")
            continue
        img = cv2.resize(img, (FRAME_WIDTH, FRAME_HEIGHT))

        # ── Pose detection ────────────────────────────────────
        img     = detector.find_pose(img, draw=False)
        lm_list = detector.find_position(img, draw=False)

        # ════════════════════════════════════════════════════════
        # PHASE 1 – Camera setup
        # ════════════════════════════════════════════════════════
        if in_setup:
            setup.draw_overlay(img, detector.results)
            if setup.check(detector.results):
                in_setup = False
                voice.say("Setup complete. Let's train!")
                logger.info("Setup complete – workout started.")

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            for ex_key, ex_cfg in EXERCISE_CONFIG.items():
                if key == ex_cfg["key"]:
                    in_setup    = False
                    current_key = ex_key
                    tracker     = ExerciseTracker(current_key)
                    break
            cv2.imshow(WINDOW_TITLE, img)
            continue

        # ════════════════════════════════════════════════════════
        # PHASE 2 – Workout
        # ════════════════════════════════════════════════════════

        # ── Auto-detect exercise ──────────────────────────────
        if auto_mode and lm_list:
            detected = classifier.update(lm_list, detector)
            if detected != current_key:
                logger.info(f"Auto-detected: {EXERCISE_CONFIG[detected]['display_name']}")
                current_key = detected
                tracker     = ExerciseTracker(current_key)

        cfg = EXERCISE_CONFIG[current_key]

        # ── Run exercise tracker ──────────────────────────────
        if lm_list:
            tracker.update(detector, img, lm_list, draw=True)
        else:
            tracker.feedback      = "No pose detected"
            tracker.low_visibility = True

        # ── Detect newly completed reps ───────────────────────
        if tracker.total_reps > prev_rep_count:
            prev_rep_count = tracker.total_reps
            flash_frames   = FLASH_DURATION

            # ML score blending
            ml_s  = _ml_score(ml_model, tracker)
            final = _blended_score(tracker.rep_score, ml_s)

            # Session recording (fix is_clean formula)
            session.record_rep(
                exercise_key = current_key,
                rep_score    = final,
                calories     = cfg["kcal_per_rep"],
                is_clean     = tracker.last_rep_was_clean,
            )

            # Dynamically accumulate feature rows across switches and auto-detect
            new_rows = tracker.get_feature_rows()
            if new_rows:
                last_row = new_rows[-1]
                # Update with the actual blended score and label
                last_row["rep_score"] = round(final, 2)
                last_row["rep_label"] = "good_rep" if final >= cfg.get("clean_depth", 70.0) else "bad_rep"
                session.add_feature_row(last_row)
                
                # Save rep to SQLite database
                try:
                    rep_id = db.save_rep(last_row)
                    inserted_rep_ids.append(rep_id)
                except Exception as e:
                    logger.error(f"Failed to save rep to database: {e}")

            # Voice coaching (correct cleared state retrieval)
            rom_ok = tracker.last_rep_min_angle <= cfg.get("rom_min_angle", 100)
            vel_hi = any(v < 60 for v in tracker.last_rep_velocity_samples[-5:]) \
                     if tracker.last_rep_velocity_samples else False
            voice.coach_rep(
                exercise_key  = current_key,
                rep_score     = final,
                is_asymmetric = tracker.is_asymmetric,
                bad_posture   = tracker.bad_posture,
                rom_ok        = rom_ok,
                velocity_high = vel_hi,
            )

        # ── FPS ───────────────────────────────────────────────
        now       = time.time()
        fps       = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        # ── Bar colour ────────────────────────────────────────
        bar_color = COLOR_GREEN if tracker.percentage >= 90 else COLOR_RED

        # ── Feedback colour ───────────────────────────────────
        if tracker.low_visibility or tracker.bad_posture or tracker.is_asymmetric:
            fb_color = COLOR_RED
        elif tracker.feedback == cfg["feedback_good"]:
            fb_color = COLOR_GREEN
        else:
            fb_color = COLOR_ORANGE

        # ── Draw UI ───────────────────────────────────────────
        draw_exercise_badge(img, cfg["display_name"], auto_mode)
        draw_progress_bar(  img, tracker.percentage, bar_color)
        draw_rep_panel(     img, tracker.total_reps,
                            tracker.clean_reps, tracker.bad_reps,
                            tracker.rep_score)
        draw_stats_panel(   img, session.total_calories,
                            session.elapsed, session.reps_per_minute)
        draw_symmetry_panel(img, tracker.symmetry_score, tracker.is_asymmetric)
        draw_form_score(    img, tracker.form_score)
        draw_stage_indicator(img, tracker.stage)
        draw_feedback(      img, tracker.feedback, fb_color)
        draw_hints(         img, auto_mode)
        draw_fps(           img, fps)

        if show_debug:
            draw_debug_overlay(img, {
                "left_angle"   : tracker.left_angle,
                "right_angle"  : tracker.right_angle,
                "avg_angle"    : tracker.avg_angle,
                "posture_angle": tracker.posture_angle,
                "velocity"     : tracker.velocity,
                "stage"        : tracker.stage,
            })

        if flash_frames > 0:
            draw_rep_quality_flash(img, tracker.rep_score)
            flash_frames -= 1

        cv2.imshow(WINDOW_TITLE, img)

        # ── Keyboard handling ─────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        for ex_key, ex_cfg in EXERCISE_CONFIG.items():
            if key == ex_cfg["key"] and ex_key != current_key:
                logger.info(f"Switched → {ex_cfg['display_name']}")
                current_key    = ex_key
                tracker        = ExerciseTracker(current_key)
                prev_rep_count = 0
                flash_frames   = 0
                break

        if key == ord('a'):
            auto_mode = not auto_mode
            logger.info(f"Auto-detect {'ON' if auto_mode else 'OFF'}")
            voice.say(f"Auto detect {'on' if auto_mode else 'off'}")

        if key == ord('d'):
            show_debug = not show_debug

        if key == ord('q'):
            break

    # ── Cleanup & summary ─────────────────────────────────────
    cap.release()
    voice.say("Workout complete. Well done!")

    # Export rep features to CSV for ML training (now uses the aggregated session list)
    session.export_csv()

    s = session.summary()

    # Save session summary to database and link reps
    try:
        session_id = db.save_session(s, EXERCISE_CONFIG[current_key]["display_name"])
        db.link_reps_to_session(session_id, inserted_rep_ids)
        logger.info(f"Workout session successfully saved to database with ID: {session_id}")
    except Exception as e:
        logger.error(f"Failed to save session to database: {e}")

    # Persist last_session.json for Streamlit dashboard
    try:
        with open("last_session.json", "w") as fh:
            json.dump({
                "exercise": EXERCISE_CONFIG[current_key]["display_name"],
                "total_reps": s["total_reps"],
                "clean_reps": s["clean_reps"],
                "bad_reps": s["bad_reps"],
                "calories": s["calories"],
                "duration_secs": s["duration_secs"],
                "avg_rep_score": s["avg_rep_score"],
                "avg_symmetry": tracker.avg_symmetry,
                "avg_form": tracker.avg_form,
                "reps_per_min": s["reps_per_min"]
            }, fh, indent=4)
        logger.info("Persisted last_session.json successfully.")
    except Exception as e:
        logger.error(f"Failed to write last_session.json: {e}")

    show_summary(
        reps          = s["total_reps"],
        clean_reps    = s["clean_reps"],
        bad_reps      = s["bad_reps"],
        calories      = s["calories"],
        elapsed_secs  = s["duration_secs"],
        exercise_name = EXERCISE_CONFIG[current_key]["display_name"],
        avg_symmetry  = tracker.avg_symmetry,
        avg_form      = tracker.avg_form,
        avg_rep_score = s["avg_rep_score"],
        reps_per_min  = s["reps_per_min"],
    )
    cv2.destroyAllWindows()
    logger.info("Session ended. Goodbye!")


if __name__ == "__main__":
    main()
