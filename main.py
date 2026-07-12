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
import argparse
import json
import logging
from logger_setup import setup_logger
import db

from config import (
    WINDOW_TITLE, FRAME_WIDTH, FRAME_HEIGHT, EXERCISE_CONFIG, MAX_CONSECUTIVE_FAILURES,
)
from frame_pipeline import FramePipeline
from utils import show_summary

logger = logging.getLogger("main")


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

    # ── Shared Processing Pipeline ──────────────────────────────
    pipeline = FramePipeline(exercise_key="squats", in_setup=in_setup)

    logger.info("AI Smart Fitness Trainer running. Use keyboard keys to interact.")

    # ════════════════════════════════════════════════════════════
    consecutive_failures = 0
    while True:
        success, img = cap.read()
        if not success:
            consecutive_failures += 1
            if args.source != "webcam" or consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                logger.warning("Frame read failed – ending session.")
                break
            logger.warning(f"Frame read failed (attempt {consecutive_failures}) – retrying…")
            continue
        consecutive_failures = 0

        img = pipeline.process_frame(img)
        cv2.imshow(WINDOW_TITLE, img)

        # ── Keyboard handling ─────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        for ex_key, ex_cfg in EXERCISE_CONFIG.items():
            if key == ex_cfg["key"] and ex_key != pipeline.current_key:
                logger.info(f"Switched → {ex_cfg['display_name']}")
                pipeline.set_exercise(ex_key)
                break

        if key == ord('a'):
            pipeline.toggle_auto_mode()

        if key == ord('d'):
            pipeline.show_debug = not pipeline.show_debug

        if key == ord('q'):
            break

    # ── Cleanup & summary ─────────────────────────────────────
    cap.release()
    if not pipeline.voice_muted:
        pipeline.voice.say("Workout complete. Well done!")

    # Export rep features to CSV for ML training
    pipeline.session.export_csv()

    s = pipeline.session.summary()

    # Save session summary to database and link reps
    try:
        session_id = db.save_session(s, EXERCISE_CONFIG[pipeline.current_key]["display_name"])
        db.save_all_reps(session_id, pipeline.session._all_feature_rows)
        logger.info(f"Workout session successfully saved to database with ID: {session_id}")
    except Exception as e:
        logger.error(f"Failed to save session to database: {e}")

    # Persist last_session.json for Streamlit dashboard
    try:
        with open("last_session.json", "w") as fh:
            json.dump({
                "exercise": EXERCISE_CONFIG[pipeline.current_key]["display_name"],
                "total_reps": s["total_reps"],
                "clean_reps": s["clean_reps"],
                "bad_reps": s["bad_reps"],
                "calories": s["calories"],
                "duration_secs": s["duration_secs"],
                "avg_rep_score": s["avg_rep_score"],
                "avg_symmetry": pipeline.tracker.avg_symmetry,
                "avg_form": pipeline.tracker.avg_form,
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
        exercise_name = EXERCISE_CONFIG[pipeline.current_key]["display_name"],
        avg_symmetry  = pipeline.tracker.avg_symmetry,
        avg_form      = pipeline.tracker.avg_form,
        avg_rep_score = s["avg_rep_score"],
        reps_per_min  = s["reps_per_min"],
    )
    cv2.destroyAllWindows()
    logger.info("Session ended. Goodbye!")


if __name__ == "__main__":
    main()
