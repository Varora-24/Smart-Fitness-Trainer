# ================================================================
#  pages/3_📹_Video_Analysis.py  –  Video-upload posture analysis
# ================================================================

import os
import tempfile

import cv2
import numpy as np
import streamlit as st

from auth import require_login
from config import EXERCISE_CONFIG
from frame_pipeline import FramePipeline

st.set_page_config(page_title="AI Fitness Trainer — Video Analysis", page_icon="📹", layout="wide")

require_login()

st.title("📹 Video Posture Analysis")
st.caption(
    "Upload a short clip of yourself performing an exercise. We'll run pose "
    "detection on every frame and give you a form score and rep breakdown "
    "— no live camera needed."
)

exercise_labels = {cfg["display_name"]: key for key, cfg in EXERCISE_CONFIG.items()}
chosen_label = st.selectbox("Which exercise is in this video?", list(exercise_labels.keys()))
uploaded = st.file_uploader("Upload video", type=["mp4", "mov", "avi"])

if uploaded and st.button("Analyze"):
    video_path = None
    output_path = None
    try:
        # Write uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.read())
            video_path = tmp.name

        pipeline = FramePipeline(
            exercise_key=exercise_labels[chosen_label],
            in_setup=False,
        )
        # Suppress voice on server-side processing
        pipeline.voice_muted = True

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            st.error("Could not open the uploaded video. Please check the file format.")
            st.stop()

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        progress = st.progress(0, text="Processing frames...")
        frame_idx = 0
        output_frames: list[np.ndarray] = []

        while True:
            success, frame = cap.read()
            if not success:
                break
            annotated = pipeline.process_frame(frame)
            output_frames.append(annotated)
            frame_idx += 1
            progress.progress(min(frame_idx / total_frames, 1.0))

        cap.release()
        progress.empty()

        summary = pipeline.get_summary()
        st.success(f"Analysis complete! Processed {frame_idx} frames.")

        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Reps", summary.get("total_reps", 0))
        col2.metric("Clean Reps", summary.get("clean_reps", 0))
        col3.metric("Bad Reps", summary.get("bad_reps", 0))
        col4.metric("Avg Rep Score", f"{summary.get('avg_rep_score', 0.0):.1f}")

        st.json(summary)

        # Write annotated output video for download
        if output_frames:
            out_h, out_w = output_frames[0].shape[:2]
            output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
            os.close(output_fd)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(output_path, fourcc, fps, (out_w, out_h))
            for f in output_frames:
                writer.write(f)
            writer.release()

            with open(output_path, "rb") as fh:
                st.download_button(
                    label="⬇️ Download Annotated Video",
                    data=fh.read(),
                    file_name="annotated_workout.mp4",
                    mime="video/mp4",
                )

    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")

    finally:
        # Clean up temp files — user-uploaded video content is sensitive by default
        if video_path and os.path.exists(video_path):
            os.unlink(video_path)
        if output_path and os.path.exists(output_path):
            os.unlink(output_path)
