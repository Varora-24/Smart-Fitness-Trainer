import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import av
import threading
import time
import cv2
import numpy as np
import core.data.db as db
from core.utils.auth import require_login

from core.tracking.frame_pipeline import FramePipeline
from core.utils.config import EXERCISE_CONFIG
from core.utils.ui_utils import display_reference_image, start_voice_polling

st.set_page_config(page_title="AI Fitness Trainer â€” Live", page_icon="ðŸ‹ï¸", layout="wide")

require_login()

# WebRTC configuration using public Google STUN server
RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})


class LiveVideoProcessor(VideoProcessorBase):
    def __init__(self) -> None:
        self.pipeline = FramePipeline(exercise_key="squats", in_setup=False)
        # Enable voice coaching for local use
        self.pipeline.voice_muted = False
        self.pipeline.is_browser = True
        
        # Asynchronous Drop-Oldest Queue Architecture:
        # Instead of synchronously blocking recv() with CPU inference inside a FIFO queue
        # (which causes recurring stutter-then-catch-up-jump backlog cycles), we maintain a
        # single-slot latest frame reference and run inference on a decoupled background thread.
        self._lock = threading.Lock()
        self._latest_input: np.ndarray | None = None
        self._latest_output: np.ndarray | None = None
        self._worker_running = True
        self._inference_thread = threading.Thread(target=self._run_inference_worker, daemon=True)
        self._inference_thread.start()
        
        # Init DB session
        try:
            import core.data.db as db
            import streamlit as st
            db.init_db()
            user_id = st.session_state.get("user_id")
            session_id = db.save_session({}, "squats", user_id=user_id)
            self.pipeline.session.session_id = session_id
        except Exception:
            pass

    def _run_inference_worker(self) -> None:
        """Decoupled daemon background loop that continuously processes only the newest available frame."""
        while self._worker_running:
            frame_to_process = None
            with self._lock:
                if self._latest_input is not None:
                    frame_to_process = self._latest_input
                    self._latest_input = None  # Consume frame, clear slot (drop older queued history)

            if frame_to_process is None:
                time.sleep(0.01)  # Brief sleep when waiting for new frame arrival
                continue

            try:
                annotated = self.pipeline.process_frame(frame_to_process)
                with self._lock:
                    self._latest_output = annotated
            except Exception:
                pass

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        orig_h, orig_w = img.shape[:2]

        # 1. Immediately drop older queued frames by overwriting the input slot with the newest frame
        with self._lock:
            self._latest_input = img
            latest_out = self._latest_output

        # 2. Return the most recent annotated output instantaneously without blocking the WebRTC stream
        if latest_out is not None:
            out = latest_out.copy()
            if out.shape[:2] != (orig_h, orig_w):
                out = cv2.resize(out, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
        else:
            out = img  # Pass through real-time camera video until first inference worker pass completes

        return av.VideoFrame.from_ndarray(out, format="bgr24")


st.title("ðŸ‹ï¸ AI Smart Fitness Trainer â€” Live")
st.caption(
    "Runs entirely in your browser session via WebRTC. Grant camera access "
    "below, then use the sidebar to pick an exercise. Voice coaching uses "
    "the Web Speech API to provide audio feedback directly in your browser."
)

col_video, col_controls = st.columns([3, 1])

with col_controls:
    st.subheader("Controls")
    exercise_labels = {cfg["display_name"]: key for key, cfg in EXERCISE_CONFIG.items()}
    chosen_label = st.selectbox("Exercise", list(exercise_labels.keys()))
    assert chosen_label is not None
    selected_key = exercise_labels[chosen_label]
    cfg = EXERCISE_CONFIG[selected_key]

    st.markdown("---")
    auto_mode = st.checkbox("Auto-detect exercise", value=False)
    show_debug = st.checkbox("Show debug overlay", value=False)
    st.caption("â„¹ï¸ Adjust exercise selection and overlay settings during live tracking.")

with col_video:
    ctx = webrtc_streamer(
        key="fitness-trainer-live",
        video_processor_factory=LiveVideoProcessor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 640, "max": 800},
                "height": {"ideal": 480, "max": 600},
                "frameRate": {"ideal": 15, "max": 15}
            }, 
            "audio": False
        },
        async_processing=True,
        video_receiver_size=1,  # Force maxsize=1 drop-oldest buffer behavior at WebRTC track layer
    )

    # â”€â”€ Populate Previously Vacant Screen Space Under Live Video â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.markdown("---")
    st.subheader(f"ðŸŽ¯ Exercise Form & Guidance: {cfg['display_name']}")
    
    CAMERA_INSTRUCTIONS = {
        "squats": "ðŸ“¸ **Camera Angle:** Place the camera at hip height, facing you from the side (profile view). Ensure your entire body from head to toe is visible.",
        "pushups": "ðŸ“¸ **Camera Angle:** Place the camera on the floor, facing you from the side. Ensure your entire body from head to toe is visible.",
        "curls": "ðŸ“¸ **Camera Angle:** Place the camera at chest height, facing you from the side (profile view). Ensure your upper body and arms are clearly visible.",
        "lunges": "ðŸ“¸ **Camera Angle:** Place the camera at waist height, facing you from the side (profile view). Ensure your entire body is visible.",
        "shoulder_press": "ðŸ“¸ **Camera Angle:** Place the camera at chest height, facing you from the front or slight angle. Ensure your upper body and arms extended overhead are fully visible."
    }

    info_col1, info_col2 = st.columns([1, 2])
    with info_col1:
        display_reference_image(cfg)
    with info_col2:
        if "description" in cfg:
            st.markdown(f"**About:** {cfg['description']}")
        if "kcal_per_rep" in cfg:
            st.markdown(f"**Est. Burn:** ðŸ”¥ `{cfg['kcal_per_rep']} kcal / rep`")
        if "angle_range" in cfg:
            lo, hi = cfg['angle_range']
            st.markdown(f"**Target Range of Motion:** ðŸ“ `{lo}Â° â€“ {hi}Â°`")
        if selected_key in CAMERA_INSTRUCTIONS:
            st.info(CAMERA_INSTRUCTIONS[selected_key])

# Push control updates into the pipeline processor state
if ctx.video_processor:
    target_key = exercise_labels[chosen_label]
    if ctx.video_processor.pipeline.current_key != target_key:
        ctx.video_processor.pipeline.set_exercise(target_key)
        
        # Create a new session in DB for the new exercise
        try:
            user_id = st.session_state.get("user_id")
            session_id = db.save_session({}, chosen_label, user_id=user_id)
            ctx.video_processor.pipeline.session.session_id = session_id
        except Exception:
            pass
    ctx.video_processor.pipeline.auto_mode = auto_mode
    ctx.video_processor.pipeline.show_debug = show_debug

    if st.button("End Session & Show Summary"):
        pipeline = ctx.video_processor.pipeline
        pipeline.session.export_csv()
        s = pipeline.get_summary()

        # Init database and update session
        try:
            if pipeline.session.session_id:
                db.update_session(pipeline.session.session_id, s)
                st.success(f"Workout session successfully finalized in database with ID: {pipeline.session.session_id}")
        except Exception as e:
            st.error(f"Failed to finalize session in database: {e}")

        # Persist last_session.json for dashboard
        try:
            import json
            with open("last_session.json", "w") as fh:
                json.dump({
                    "exercise": EXERCISE_CONFIG[pipeline.current_key]["display_name"],
                    "total_reps": s["total_reps"],
                    "clean_reps": s["clean_reps"],
                    "bad_reps": s["bad_reps"],
                    "calories": s["calories"],
                    "duration_secs": s["duration_secs"],
                    "avg_rep_score": s["avg_rep_score"],
                    "avg_symmetry": s["avg_symmetry"],
                    "avg_form": s["avg_form"],
                    "reps_per_min": s["reps_per_min"]
                }, fh, indent=4)
        except Exception as e:
            st.error(f"Failed to write last_session.json: {e}")

        st.subheader("ðŸ“Š Session Summary")
        st.json(s)

# â”€â”€ Web Speech API Voice Coaching Bridge â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if ctx.video_processor:
    start_voice_polling(ctx.video_processor, key_prefix="live_trainer", is_yoga=False)
