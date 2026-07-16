# ================================================================
#  pages/3_📹_Video_Analysis.py  –  Video-upload posture analysis
#  Full analysis dashboard: per-rep table, form charts, summary
# ================================================================

import os
import tempfile
import time

import cv2
import numpy as np
import pandas as pd
import streamlit as st

import db
from auth import require_login
from config import EXERCISE_CONFIG
from frame_pipeline import FramePipeline

st.set_page_config(
    page_title="AI Fitness Trainer — Video Analysis",
    page_icon="📹",
    layout="wide",
)

require_login()

# ── Page header ─────────────────────────────────────────────────
st.title("📹 Video Posture Analysis")
st.caption(
    "Upload a workout clip and get a complete AI-powered breakdown — "
    "rep count, good/bad rep split, calories burned, per-rep form scores, "
    "and a downloadable annotated video."
)

st.info(
    "📌 **Tips for best results**: film yourself from the side or front, "
    "ensure your full body is visible, use good lighting, and keep clips "
    "under 3 minutes for fastest processing.",
    icon="📌",
)

st.markdown("---")

# ── Controls ─────────────────────────────────────────────────────
col_sel, col_up = st.columns([1, 2])

with col_sel:
    exercise_labels = {cfg["display_name"]: key for key, cfg in EXERCISE_CONFIG.items()}
    chosen_label = st.selectbox(
        "🏋️ Which exercise is in this video?",
        list(exercise_labels.keys()),
        help="Select the exercise so the AI uses the correct form thresholds.",
    )
    exercise_key = exercise_labels[chosen_label]
    kcal_per_rep = float(EXERCISE_CONFIG[exercise_key].get("kcal_per_rep", 0.25))

with col_up:
    uploaded = st.file_uploader(
        "🎬 Upload your workout video",
        type=["mp4", "mov", "avi", "mkv"],
        help="Max 200 MB. Supported formats: MP4, MOV, AVI, MKV",
    )

if not uploaded:
    st.markdown("---")
    st.markdown(
        """
        ### What you'll get after analysis:
        | 📊 Metric | Description |
        |---|---|
        | **Total Reps** | All completed repetitions detected |
        | **✅ Good Reps** | Reps scored ≥ 75/100 — correct form |
        | **❌ Bad Reps** | Reps below 75 — form corrections flagged |
        | **🔥 Calories** | Estimated calories based on exercise & rep count |
        | **⏱️ Duration** | Total video processing time |
        | **📈 Avg Form Score** | Overall quality across all reps |
        | **Per-Rep Breakdown** | Symmetry, Range of Motion, Posture, Control per rep |
        | **🎬 Annotated Video** | Downloadable video with pose overlay & score badges |
        """
    )
    st.stop()

# ── Analyze button ───────────────────────────────────────────────
if not st.button("🚀 Analyze Video", type="primary", use_container_width=True):
    st.stop()

video_path = None
output_path = None

try:
    # ── Write temp input file ─────────────────────────────────
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(uploaded.read())
        video_path = tmp.name

    # ── Open video ────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.error("❌ Could not open the uploaded video. Please check the file format and try again.")
        st.stop()

    src_fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frms = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    duration_s = total_frms / src_fps

    st.markdown("---")
    with st.spinner(f"🔍 Analysing {int(duration_s)}s of video — this may take a moment…"):

        # ── Init pipeline ─────────────────────────────────────
        pipeline = FramePipeline(exercise_key=exercise_key, in_setup=False)
        pipeline.voice_muted = True   # no TTS on server

        progress_bar = st.progress(0, text="Processing frames…")

        frame_idx     = 0
        output_frames: list[np.ndarray] = []
        start_wall    = time.time()

        while True:
            ok, frame = cap.read()
            if not ok:
                break
            annotated = pipeline.process_frame(frame)
            output_frames.append(annotated)
            frame_idx += 1
            if frame_idx % 10 == 0:
                progress_bar.progress(
                    min(frame_idx / total_frms, 1.0),
                    text=f"Processing frame {frame_idx}/{total_frms}…",
                )

        cap.release()
        progress_bar.empty()
        wall_time = time.time() - start_wall

    summary = pipeline.get_summary()
    feature_rows: list[dict] = pipeline.session._all_feature_rows  # rep-level data

    # ─────────────────────────────────────────────────────────────
    # ── RESULTS DASHBOARD ────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    st.success(f"✅ Analysis complete — {frame_idx} frames processed in {wall_time:.1f}s")
    st.markdown("---")

    total_reps  = summary.get("total_reps", 0)
    clean_reps  = summary.get("clean_reps", 0)
    bad_reps    = summary.get("bad_reps", 0)
    calories    = round(total_reps * kcal_per_rep, 2)
    avg_score   = summary.get("avg_rep_score", 0.0)
    avg_sym     = summary.get("avg_symmetry", 0.0)
    avg_form    = summary.get("avg_form", 0.0)

    # ── Top metric cards ─────────────────────────────────────────
    st.subheader("📊 Session Summary")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🏋️ Exercise",    chosen_label)
    c2.metric("🔢 Total Reps",  total_reps)
    c3.metric("✅ Good Reps",   clean_reps,
              delta=f"+{clean_reps}" if clean_reps else None)
    c4.metric("❌ Bad Reps",    bad_reps,
              delta=f"-{bad_reps}" if bad_reps else None,
              delta_color="inverse")
    c5.metric("🔥 Calories",    f"{calories} kcal")
    c6.metric("📈 Avg Score",   f"{avg_score:.1f}/100")

    st.markdown("---")

    # ── Form quality breakdown ────────────────────────────────────
    st.subheader("🧠 Form Quality Breakdown")

    if feature_rows:
        df = pd.DataFrame(feature_rows)

        # Rename for display
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
            lambda x: "✅ Good" if x == "good_rep" else "❌ Bad"
        )

        # ── Per-rep score chart ───────────────────────────────────
        chart_cols = [c for c in ["Symmetry", "Range of Motion", "Posture", "Control"] if c in df_display.columns]
        if chart_cols:
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("**📉 Per-Rep Score Trend**")
                if "Rep Score" in df_display.columns:
                    score_df = df_display[["Rep #", "Rep Score"]].set_index("Rep #")
                    st.line_chart(score_df, height=220)

            with col_chart2:
                st.markdown("**📊 Avg Form Dimensions**")
                avgs = {col: float(df_display[col].mean()) for col in chart_cols}
                avg_df = pd.DataFrame.from_dict(avgs, orient="index", columns=["Score"])
                st.bar_chart(avg_df, height=220)

        # ── Good vs Bad rep donut style ──────────────────────────
        col_g, col_b = st.columns(2)
        with col_g:
            good_pct = round(clean_reps / total_reps * 100) if total_reps else 0
            st.metric("Good Rep Rate", f"{good_pct}%",
                      help="Percentage of reps with form score ≥ 75")

        with col_b:
            st.metric(
                "Weakest Dimension",
                min(avgs, key=avgs.get) if chart_cols else "N/A",
                help="The form dimension needing the most attention",
            )

        # ── Avg per-dimension table ───────────────────────────────
        st.markdown("**🏅 Average Scores per Dimension (0–100)**")
        dim_cols = st.columns(len(chart_cols))
        for i, col_name in enumerate(chart_cols):
            val = avgs.get(col_name, 0.0)
            color = "🟢" if val >= 75 else "🟡" if val >= 50 else "🔴"
            dim_cols[i].metric(f"{color} {col_name}", f"{val:.1f}")

        st.markdown("---")

        # ── Per-rep detail table ─────────────────────────────────
        st.subheader("📋 Per-Rep Detail Table")
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

        # ── Coaching tips based on weakest dimension ─────────────
        st.markdown("---")
        st.subheader("💡 AI Coaching Tips")
        if chart_cols:
            weakest = min(avgs, key=avgs.get)
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
            st.info(f"🎯 **Focus Area: {weakest}** — {tip}", icon="🎯")

    else:
        st.warning(
            "No reps were detected in this video. Make sure your full body is visible "
            "and you completed at least one full repetition.",
            icon="⚠️",
        )

    # ── Annotated video download ──────────────────────────────────
    st.markdown("---")
    st.subheader("🎬 Annotated Video")

    if output_frames:
        out_h, out_w = output_frames[0].shape[:2]
        out_fd, output_path = tempfile.mkstemp(suffix=".mp4")
        os.close(out_fd)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, src_fps, (out_w, out_h))
        for f in output_frames:
            writer.write(f)
        writer.release()

        with open(output_path, "rb") as fh:
            video_bytes = fh.read()

        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            st.download_button(
                label="⬇️ Download Annotated Video",
                data=video_bytes,
                file_name=f"annotated_{exercise_key}_{int(time.time())}.mp4",
                mime="video/mp4",
                use_container_width=True,
            )
        with col_info:
            size_mb = len(video_bytes) / 1_048_576
            st.caption(
                f"Video contains pose skeleton overlay, rep counter, form score badge, "
                f"and stage indicator on every frame. "
                f"File size: {size_mb:.1f} MB"
            )

    # ── Save session to DB ────────────────────────────────────────
    user_id = st.session_state.get("user_id")
    if user_id and total_reps > 0:
        try:
            session_id = db.save_session(summary, exercise_key, user_id)
            if session_id:
                db.update_session(session_id, {**summary, "calories": calories})
            st.caption("✅ Session saved to your workout history.")
        except Exception:
            pass   # Non-fatal: don't interrupt the results display

except Exception as exc:
    st.error(f"❌ An error occurred during analysis: {exc}")
    raise

finally:
    if video_path and os.path.exists(video_path):
        os.unlink(video_path)
    if output_path and os.path.exists(output_path):
        os.unlink(output_path)
