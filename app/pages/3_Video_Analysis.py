import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ================================================================
#  pages/3_📹_Video_Analysis.py  –  Video-upload posture analysis
#  Full analysis dashboard: per-rep table, form charts, summary
# ================================================================

import gc
import os
import tempfile
import time

import cv2
import pandas as pd
import streamlit as st

import core.data.db as db
from core.utils.auth import require_login
from core.utils.config import EXERCISE_CONFIG, YOGA_POSE_CONFIG
from core.tracking.pose_module import PoseDetector
from core.tracking.yoga_tracker import YogaPoseTracker
from core.tracking.frame_pipeline import FramePipeline
from core.tracking.exercise_classifier import ExerciseClassifier

st.set_page_config(
    page_title="AI Fitness Trainer — Video Analysis",
    layout="wide",
)
from core.utils.icons import ui_alert, get_icon_html  # noqa: E402

require_login()

# ── Page header ─────────────────────────────────────────────────
st.markdown(f"<h1>{get_icon_html('video', size=36)} Video Posture Analysis</h1>", unsafe_allow_html=True)
st.caption(
    "Upload a workout clip and get a complete AI-powered breakdown — "
    "rep count, good/bad rep split, calories burned, per-rep form scores, "
    "and a downloadable annotated video."
)

# ── Video quality guidance ────────────────────────────────────────
with st.expander("Video Requirements & Tips for Best Results", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
**{get_icon_html('circle-check', size=16)} Recommended Settings**
- **Aspect ratio:** 16:9 landscape (horizontal recording)
- **Minimum resolution:** 720p (1280×720)
- **Frame rate:** 24fps or higher
- **Maximum duration:** 90 seconds
- **File size:** Under 100 MB

**{get_icon_html('camera', size=16)} Camera Placement**
- Place camera at **hip/chest height** for most exercises
- Ensure your **entire body** is in frame (head to toe)
- Good lighting — avoid backlit setups
- Solid, non-patterned background helps detection
""", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
**{get_icon_html('smartphone', size=16)} Portrait Videos (9:16) — Supported!**
We automatically add black bars (letterboxing) to portrait videos
so your body proportions are preserved and the AI reads angles correctly.
No stretching or distortion.

**Required body visibility per exercise:**
| Exercise | Minimum Required |
|---|---|
| Squats | Full body (head to toe) |
| Lunges | Full body (head to toe) |
| Push-ups | Upper body + torso (hips) |
| Shoulder Press | Upper body + arms overhead |
| Bicep Curls | Upper body (shoulders to wrists) |
""", unsafe_allow_html=True)

st.markdown("---")

# ── Controls ─────────────────────────────────────────────────────
col_sel, col_up = st.columns([1, 2])

with col_sel:
    mode = st.radio("Category", ["Rep-Based Exercise", "Hold-Based Yoga"], horizontal=True)
    is_yoga = mode == "Hold-Based Yoga"

    if not is_yoga:
        exercise_labels = {cfg["display_name"]: key for key, cfg in EXERCISE_CONFIG.items()}
        chosen_label = st.selectbox(
            "Which exercise is in this video?",
            list(exercise_labels.keys()),
            help="Select the exercise so the AI uses the correct form thresholds.",
        )
        assert chosen_label is not None
        selected_key = exercise_labels[chosen_label]
        kcal_per_rep = float(EXERCISE_CONFIG[selected_key].get("kcal_per_rep", 0.25))

        CAMERA_INSTRUCTIONS = {
            "squats": f"{get_icon_html('camera', size=16)} **Camera Angle:** Side profile, hip height, full body head-to-toe visible.",
            "pushups": f"{get_icon_html('camera', size=16)} **Camera Angle:** Side profile at floor level, full body visible.",
            "curls": f"{get_icon_html('camera', size=16)} **Camera Angle:** Side profile at chest height, upper body & arms visible.",
            "lunges": f"{get_icon_html('camera', size=16)} **Camera Angle:** Side profile at waist height, full body visible.",
            "shoulder_press": f"{get_icon_html('camera', size=16)} **Camera Angle:** Front-facing or slight angle, full overhead extension visible.",
        }

        if selected_key in CAMERA_INSTRUCTIONS:
            ui_alert(CAMERA_INSTRUCTIONS[selected_key], type="info")
    else:
        yoga_labels = {cfg["display_name"]: key for key, cfg in YOGA_POSE_CONFIG.items()}
        chosen_label = st.selectbox(
            "Which yoga pose is in this video?",
            list(yoga_labels.keys()),
        )
        assert chosen_label is not None
        selected_key = yoga_labels[chosen_label]
        ui_alert(f"{get_icon_html('camera', size=16)} **Camera Angle:** Position the camera at hip/chest height, facing you from the front or slight angle. Ensure your entire body is visible.", type="info")


with col_up:
    uploaded = st.file_uploader(
        "Upload your workout video",
        type=["mp4", "mov", "avi", "mkv"],
        help="Max 100 MB · Max 90 seconds · Supported: MP4, MOV, AVI, MKV",
    )

if not uploaded:
    st.markdown("---")
    st.markdown(
        f"""
        ### What you'll get after analysis:
        | Metric | Description |
        |---|---|
        | **Total Reps** | All completed repetitions detected |
        | **{get_icon_html('circle-check', size=16)} Good Reps** | Reps scored ≥ 60/100 — correct form |
        | **{get_icon_html('circle-x', size=16)} Bad Reps** | Reps below 60 — form corrections flagged |
        | **{get_icon_html('flame', size=16)} Calories** | Estimated calories based on exercise & rep count |
        | **{get_icon_html('clock', size=16)} Duration** | Total video processing time |
        | **{get_icon_html('trending-up', size=16)} Avg Form Score** | Overall quality across all reps |
        | **Per-Rep Breakdown** | Symmetry, Range of Motion, Posture, Control per rep |
        | **{get_icon_html('film', size=16)} Annotated Video** | Downloadable video with pose overlay & score badges |
        """, unsafe_allow_html=True
    )
    st.stop()

# ── Analyze button ───────────────────────────────────────────────
if not st.button("Analyze Video", type="primary", use_container_width=True):
    st.stop()

video_path  = None
output_path = None
pipeline    = None

try:
    # ── Check Upload Rate Limit ───────────────────────────────
    user_id = st.session_state.get("user_id")
    if user_id:
        allowed, err_reason = db.check_upload_limit(user_id, limit=5)
        if not allowed:
            if err_reason == "limit_exceeded":
                ui_alert("You've reached the hourly upload limit (5/hour). Please try again later.", type="error")
            else:
                ui_alert("Couldn't verify upload eligibility right now, please try again.", type="error")
            st.stop()
        # Log this attempt immediately so it counts towards the limit
        db.log_upload(user_id)

    # ── Write temp input file ─────────────────────────────────
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded.read())
        video_path = tmp.name

    # ── Validate file size ────────────────────────────────────
    size_mb = os.path.getsize(video_path) / 1_048_576
    if size_mb > 100:
        ui_alert(
            f"Video is {size_mb:.0f} MB — the limit is 100 MB. "
            "Please trim your clip and try again.", type="error"
        )
        st.stop()

    # ── Open video ────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        ui_alert("Could not open the uploaded video. Please check the file format and try again.", type="error")
        st.stop()

    src_fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frms = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    src_w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = total_frms / src_fps

    # ── Validate duration ─────────────────────────────────────
    if duration_s > 90:
        ui_alert(
            f"Video is {duration_s:.0f}s long — the limit is 90 seconds. "
            "Please trim your clip. Longer videos will exceed cloud memory limits.", type="error"
        )
        cap.release()
        st.stop()

    # ── Notify if portrait / non-16:9 ────────────────────────
    src_ratio = src_w / src_h if src_h > 0 else 1.0
    if src_ratio < 1.1:   # portrait or nearly square
        ui_alert(
            f"Detected a portrait/square video ({src_w}×{src_h}). "
            "Black bars will be added automatically — no distortion to your pose.",
            type="info"
        )
    elif abs(src_ratio - 16/9) > 0.1:
        ui_alert(
            f"Non-standard aspect ratio detected ({src_w}×{src_h}, {src_ratio:.2f}:1). "
            "Letterboxing applied automatically.",
            type="info"
        )

    st.markdown("---")
    with st.spinner(f"Analysing {int(duration_s)}s of video — using VIDEO tracking mode for best accuracy…"):

        # ── Init pipeline in VIDEO mode ───────────────────────
        # VIDEO mode gives MediaPipe temporal continuity across frames,
        # dramatically improving detection on recorded clips.
        if is_yoga:
            detector = PoseDetector(video_mode=True)
            yoga_tracker = YogaPoseTracker(selected_key)
            yoga_scores = []
            pipeline = None
        else:
            pipeline = FramePipeline(exercise_key=selected_key, in_setup=False, video_mode=True)
            pipeline.voice_muted = True   # No audio in video analysis
            detector = None
            yoga_tracker = None
            yoga_scores = []

        # ── Open output video writer ──────────────────────────
        # CRITICAL: Stream frames directly to disk — never accumulate in RAM.
        # A 30-second 1280×720 video = ~2.5 GB in-memory. This would OOM the server.
        out_fd, output_path = tempfile.mkstemp(suffix=".mp4")
        os.close(out_fd)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_w, out_h = 1280, 720
        writer = cv2.VideoWriter(output_path, fourcc, min(src_fps, 30.0), (out_w, out_h))

        progress_bar = st.progress(0, text="Processing frames…")

        frame_idx   = 0
        start_wall  = time.time()

        # ── Wrong-exercise early detection buffer ─────────────
        # Collect landmark data from first 90 frames to cross-check exercise.
        classifier_lm_samples: list = []
        classifier = ExerciseClassifier()

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Pass src_fps so the pipeline computes accurate timestamps for VIDEO mode
            if is_yoga and detector and yoga_tracker:
                timestamp_ms = int(frame_idx * 1000 / max(src_fps, 1.0))
                frame_lb = FramePipeline._letterbox(frame, out_w, out_h)
                img = detector.find_pose(frame_lb, draw=False, timestamp_ms=timestamp_ms)
                lm_list = detector.find_position(img, draw=False)
                yoga_tracker.update(detector, img, lm_list, draw=True)
                annotated = img
                if yoga_tracker.alignment_score > 0:
                    yoga_scores.append({
                        "frame": frame_idx,
                        "time_s": frame_idx / src_fps,
                        "score": yoga_tracker.alignment_score
                    })
            else:
                annotated = pipeline.process_frame(frame, src_fps=src_fps)
                
            writer.write(annotated)

            # Collect for wrong-exercise detection (first 90 frames only)
            if not is_yoga and frame_idx < 90 and pipeline.detector.lm_list:
                classifier_lm_samples.append(pipeline.detector.lm_list)

            frame_idx += 1
            if frame_idx % 15 == 0:
                progress_bar.progress(
                    min(frame_idx / total_frms, 1.0),
                    text=f"Processing frame {frame_idx}/{total_frms}…",
                )

        cap.release()
        writer.release()
        progress_bar.empty()
        wall_time = time.time() - start_wall

    if not is_yoga:
        summary      = pipeline.get_summary()
        feature_rows: list[dict] = pipeline.session._all_feature_rows
    else:
        summary = {}
        feature_rows = []

    # ─────────────────────────────────────────────────────────────
    # ── WRONG EXERCISE DETECTION ─────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    if classifier_lm_samples:
        # Run classifier on collected samples
        detected_exercise = selected_key   # default to user's selection
        vote_counts: dict[str, int] = {}
        for lm_list in classifier_lm_samples:
            detected = classifier.update(lm_list, pipeline.detector)
            vote_counts[detected] = vote_counts.get(detected, 0) + 1

        if vote_counts:
            top_detected = max(vote_counts, key=vote_counts.get)  # type: ignore[arg-type]
            top_count = vote_counts[top_detected]
            confidence = top_count / len(classifier_lm_samples)

            if top_detected != selected_key and confidence > 0.55:
                top_label = EXERCISE_CONFIG[top_detected]["display_name"]
                ui_alert(
                    f"**Possible Exercise Mismatch!** \n\n"
                    f"Our AI detected **{top_label}** movements in your video "
                    f"(confidence: {confidence*100:.0f}%), but you selected "
                    f"**{chosen_label}**.\n\n"
                    f"If this is wrong, cancel and re-upload with the correct exercise "
                    f"selected to get accurate rep counts and form scores.",
                    type="warning"
                )

    # ─────────────────────────────────────────────────────────────
    # ── RESULTS DASHBOARD ────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    ui_alert(f"Analysis complete — {frame_idx} frames processed in {wall_time:.1f}s", type="success")
    st.markdown("---")

    total_reps  = summary.get("total_reps", 0)
    clean_reps  = summary.get("clean_reps", 0)
    bad_reps    = summary.get("bad_reps", 0)
    calories    = round(total_reps * kcal_per_rep, 2)
    avg_score   = summary.get("avg_rep_score", 0.0)
    avg_sym     = summary.get("avg_symmetry", 0.0)
    avg_form    = summary.get("avg_form", 0.0)

    # ── Top metric cards ─────────────────────────────────────────
    st.markdown(f"<h3>{get_icon_html('chart-bar', size=24)} Session Summary</h3>", unsafe_allow_html=True)
    if is_yoga:
        c1, c2, c3 = st.columns(3)
        avg_yoga_score = sum(s["score"] for s in yoga_scores) / len(yoga_scores) if yoga_scores else 0
        held_secs = len(yoga_scores) / src_fps if src_fps else 0
        c1.metric("Pose", chosen_label)
        c2.metric("Duration Held", f"{held_secs:.1f}s")
        c3.metric("Avg Alignment", f"{avg_yoga_score:.1f}%")
    else:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Exercise",    chosen_label)
        c2.metric("Total Reps",  total_reps)
        c3.metric("Good Reps",   clean_reps,
                  delta=f"+{clean_reps}" if clean_reps else None)
        c4.metric("Bad Reps",    bad_reps,
                  delta=f"-{bad_reps}" if bad_reps else None,
                  delta_color="inverse")
        c5.metric("Calories",    f"{calories} kcal")
        c6.metric("Avg Score",   f"{avg_score:.1f}/100")

    st.markdown("---")

    # ── Form quality breakdown ────────────────────────────────────
    st.markdown(f"<h3>{get_icon_html('brain', size=24)} Form Quality Breakdown</h3>", unsafe_allow_html=True)

    if is_yoga and yoga_scores:
        df = pd.DataFrame(yoga_scores)
        st.line_chart(df.set_index("time_s")["score"], height=250)
        st.caption("Alignment score over time (seconds). Consistently staying above the threshold is key.")
        
    elif not is_yoga and feature_rows:
        df = pd.DataFrame(feature_rows)

        rename_map = {
            "symmetry": "Symmetry",
            "range_of_motion": "Range of Motion",
            "posture": "Posture",
            "control": "Control",
            "rep_score": "Rep Score",
            "rep_label": "Quality",
        }
        df_display = df.rename(columns=rename_map)
        df_display["Rep #"] = range(1, len(df_display) + 1)
        df_display["Quality"] = df_display.get("Quality", "").apply(
            lambda x: "Good" if x == "good_rep" else "Bad"
        )

        chart_cols = [c for c in ["Symmetry", "Range of Motion", "Posture", "Control"] if c in df_display.columns]
        if chart_cols:
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown(f"**{get_icon_html('trending-down', size=18)} Per-Rep Score Trend**", unsafe_allow_html=True)
                if "Rep Score" in df_display.columns:
                    score_df = df_display[["Rep #", "Rep Score"]].set_index("Rep #")
                    st.line_chart(score_df, height=220)

            with col_chart2:
                st.markdown(f"**{get_icon_html('chart-bar', size=18)} Avg Form Dimensions**", unsafe_allow_html=True)
                avgs = {col: float(df_display[col].mean()) for col in chart_cols}
                avg_df = pd.DataFrame.from_dict(avgs, orient="index", columns=["Score"])
                st.bar_chart(avg_df, height=220)

        col_g, col_b = st.columns(2)
        with col_g:
            good_pct = round(clean_reps / total_reps * 100) if total_reps else 0
            st.metric("Good Rep Rate", f"{good_pct}%",
                      help="Percentage of reps with form score ≥ 60")

        with col_b:
            if chart_cols:
                avgs_local = {col: float(df_display[col].mean()) for col in chart_cols}
                st.metric(
                    "Weakest Dimension",
                    min(avgs_local, key=avgs_local.get),  # type: ignore[arg-type]
                    help="The form dimension needing the most attention",
                )

        st.markdown(f"**{get_icon_html('medal', size=18)} Average Scores per Dimension (0–100)**", unsafe_allow_html=True)
        if chart_cols:
            avgs_final = {col: float(df_display[col].mean()) for col in chart_cols}
            dim_cols = st.columns(len(chart_cols))
            for i, col_name in enumerate(chart_cols):
                val = avgs_final.get(col_name, 0.0)
                dim_cols[i].metric(f"{col_name}", f"{val:.1f}")

        st.markdown("---")

        st.markdown(f"<h3>{get_icon_html('list', size=24)} Per-Rep Detail Table</h3>", unsafe_allow_html=True)
        display_cols = ["Rep #", "Quality", "Rep Score"] + chart_cols
        display_cols = [c for c in display_cols if c in df_display.columns]
        st.dataframe(
            df_display[display_cols].style.format(
                {col: "{:.1f}" for col in chart_cols + ["Rep Score"] if col in df_display.columns}
            ).background_gradient(subset=["Rep Score"] if "Rep Score" in display_cols else [],
                                  cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")
        st.markdown(f"<h3>{get_icon_html('lightbulb', size=24)} AI Coaching Tips</h3>", unsafe_allow_html=True)
        if chart_cols:
            avgs_tips = {col: float(df_display[col].mean()) for col in chart_cols}
            weakest = min(avgs_tips, key=avgs_tips.get)  # type: ignore[arg-type]
            TIPS = {
                "Symmetry": (
                    "**Symmetry needs work.** Your left and right sides are moving unevenly. "
                    "Focus on using both limbs equally. Try single-arm or single-leg "
                    "variations to isolate and correct the weaker side."
                ),
                "Range of Motion": (
                    "**Incomplete range of motion.** You're not reaching full extension or "
                    "flexion. Go slower and concentrate on reaching the full range — quality "
                    "over quantity. Consider mobility warm-ups before your next session."
                ),
                "Posture": (
                    "**Posture needs attention.** Your spine/torso alignment is drifting. "
                    "Keep your core braced and your back neutral throughout the movement. "
                    "Recording yourself side-on can help identify the exact fault."
                ),
                "Control": (
                    "**Movement control is low.** You may be moving too fast or bouncing at "
                    "the end range. Slow the eccentric (lowering) phase to 3 seconds for "
                    "better muscle engagement and form control."
                ),
            }
            tip = TIPS.get(weakest, "Keep practising — consistency is key!")
            ui_alert(f"**Focus Area: {weakest}** — {tip}", type="info")

    else:
        ui_alert(
            "No reps were detected in this video. Common reasons:\n"
            "- Full body not visible in frame (especially lower body)\n"
            "- Wrong exercise selected — check for the mismatch warning above\n"
            "- Video too short to complete a full repetition\n"
            "- Very fast movement causing pose detection to struggle\n\n"
            "Try re-recording from the side with your entire body visible.",
            type="warning"
        )

    # ── Annotated video download ──────────────────────────────────
    st.markdown("---")
    st.markdown(f"<h3>{get_icon_html('film', size=24)} Annotated Video</h3>", unsafe_allow_html=True)

    if output_path and os.path.exists(output_path):
        with open(output_path, "rb") as fh:
            video_bytes = fh.read()

        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            st.download_button(
                label="Download Annotated Video",
                data=video_bytes,
                file_name=f"annotated_{selected_key}_{int(time.time())}.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        with col_info:
            size_mb_out = len(video_bytes) / 1_048_576
            st.caption(
                f"Video contains pose skeleton overlay, rep counter, form score badge, "
                f"and stage indicator on every frame. "
                f"File size: {size_mb_out:.1f} MB"
            )
        del video_bytes   # free memory immediately after creating download button

    # ── Save session to DB ────────────────────────────────────────
    user_id = st.session_state.get("user_id")
    if user_id and total_reps > 0:
        try:
            session_id = db.save_session(summary, selected_key, user_id)
            if session_id:
                db.update_session(session_id, {**summary, "calories": calories})
            st.markdown(f"<div style='font-size: 0.875rem; color: #9CA3AF;'>{get_icon_html('circle-check', size=16)} Session saved to your workout history.</div>", unsafe_allow_html=True)
        except Exception as e:
            import logging
            logging.warning(f"Non-fatal error saving session: {e}")

except Exception as exc:
    ui_alert(f"An error occurred during analysis: {exc}", type="error")
    raise

finally:
    # ── Aggressive memory cleanup ─────────────────────────────────
    if pipeline is not None:
        del pipeline
    if video_path and os.path.exists(video_path):
        os.unlink(video_path)
    if output_path and os.path.exists(output_path):
        try:
            os.unlink(output_path)
        except Exception as e:
            import logging
            logging.warning(f'Ignored exception in 3_📹_Video_Analysis.py: {e}')
    gc.collect()
