"""
6_🧘_Yoga.py — Yoga Hold-Tracking Page
=======================================
Uses the same WebRTC / FramePipeline infrastructure as the Live Trainer
but routes pose-detection output to YogaPoseTracker instead of ExerciseTracker.
No rep-counting — tracks alignment score and hold duration per pose.
"""

from __future__ import annotations


import av
import numpy as np
import streamlit as st
from streamlit_webrtc import VideoProcessorBase, webrtc_streamer, RTCConfiguration

from core.utils.auth import require_login
from core.utils.config import YOGA_POSE_CONFIG
from app.ui_utils import display_reference_image
from core.tracking.frame_pipeline import FramePipeline
from core.tracking.yoga_tracker import YogaPoseTracker
from core.tracking.surya_namaskar_tracker import SuryaNamaskarTracker, SURYA_NAMASKAR_STEPS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Fitness Trainer — Yoga",
    page_icon="🧘",
    layout="wide",
)

require_login()

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# ── Session state defaults ────────────────────────────────────────────────────
if "yoga_pose_key" not in st.session_state:
    st.session_state["yoga_pose_key"] = "mountain_pose"
if "yoga_completed" not in st.session_state:
    st.session_state["yoga_completed"] = []


# ── WebRTC Video Processor ────────────────────────────────────────────────────
class YogaVideoProcessor(VideoProcessorBase):
    """
    Processes WebRTC frames for yoga hold detection.
    Shares PoseDetector plumbing via FramePipeline (in_setup=False,
    video_mode=False) but routes landmarks to YogaPoseTracker, not
    ExerciseTracker. No rep state machine runs.
    """

    def __init__(self) -> None:
        # Use FramePipeline only for pose detection + drawing infrastructure.
        # ExerciseTracker is still initialised inside FramePipeline but is
        # never called from this processor — we call yoga_tracker.update() only.
        self._pipeline = FramePipeline(exercise_key="squats", in_setup=False,
                                       video_mode=False)
        self._pipeline.voice_muted = False
        self._pipeline.is_browser  = True
        # Safe pose key passing from main thread
        self.pending_yoga_key: str | None = None
        self._yoga_key     = "mountain_pose"
        self._yoga_tracker = YogaPoseTracker(self._yoga_key)
        self._surya_tracker = SuryaNamaskarTracker()
        self.mode: str = "single_pose"
        self.pending_mode: str | None = None
        self.current_step_idx: int = 0

        # Frame-skip: run MediaPipe inference every 4th frame for stability,
        # hold last annotated frame for the skipped frames.
        self._skip_n   = 4
        self._frame_idx = 0
        self._last_out: "np.ndarray | None" = None

        # Shared state (read by the main thread for UI display)
        self.alignment_score:     float = 0.0
        self.hold_duration_secs:  float = 0.0
        self.is_holding:          bool  = False
        self.active_feedback:     str   = ""
        self.pose_completed:      bool  = False

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        orig_h, orig_w = img.shape[:2]

        # Swap mode or pose if the main thread set pending updates
        if self.pending_mode is not None:
            if self.pending_mode != self.mode:
                self.mode = self.pending_mode
                if self.mode == "surya_namaskar":
                    self._surya_tracker.reset_sequence()
            self.pending_mode = None

        if self.pending_yoga_key is not None:
            if self.pending_yoga_key != self._yoga_key:
                self._yoga_key     = self.pending_yoga_key
                self._yoga_tracker = YogaPoseTracker(self.pending_yoga_key)
            self.pending_yoga_key = None

        # Inference every 4th frame, render every frame
        if self._frame_idx % self._skip_n == 0 or self._last_out is None:
            # Use FramePipeline's pose detector to get lm_list
            img = self._pipeline.detector.find_pose(img, draw=False)
            lm_list = self._pipeline.detector.find_position(img, draw=False)

            if self.mode == "surya_namaskar":
                self._surya_tracker.update(
                    detector=self._pipeline.detector,
                    img=img,
                    lm_list=lm_list,
                    draw=True,
                )
                self.alignment_score    = self._surya_tracker.alignment_score
                self.hold_duration_secs = self._surya_tracker.hold_duration_secs
                self.is_holding         = self._surya_tracker.is_holding_correctly
                self.active_feedback    = self._surya_tracker.active_feedback
                self.pose_completed     = self._surya_tracker.sequence_completed
                self.current_step_idx   = self._surya_tracker.step_idx
            else:
                self._yoga_tracker.update(
                    detector=self._pipeline.detector,
                    img=img,
                    lm_list=lm_list,
                    draw=True,
                )
                self.alignment_score    = self._yoga_tracker.alignment_score
                self.hold_duration_secs = self._yoga_tracker.hold_duration_secs
                self.is_holding         = self._yoga_tracker.is_holding_correctly
                self.active_feedback    = self._yoga_tracker.active_feedback
                self.pose_completed     = self._yoga_tracker.pose_completed

            self._last_out = img.copy()

        self._frame_idx = (self._frame_idx + 1) % self._skip_n
        out = self._last_out.copy()
        if out.shape[:2] != (orig_h, orig_w):
            import cv2
            out = cv2.resize(out, (orig_w, orig_h))
        return av.VideoFrame.from_ndarray(out, format="bgr24")


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🧘 AI Yoga Coach — Hold & Align")
st.caption(
    "Select a pose, position yourself in front of the camera, and hold it "
    "correctly for the required duration. Your alignment is scored in real-time "
    "using the same MediaPipe skeleton used by the Live Trainer."
)

# ── Sidebar: mode and pose selector ───────────────────────────────────────────
with st.sidebar:
    st.header("Practice Mode")
    practice_mode = st.radio(
        "Select Mode",
        ["Single Pose Practice", "Surya Namaskar Sequence"],
        index=0,
        horizontal=True,
    )
    mode_key = "surya_namaskar" if practice_mode == "Surya Namaskar Sequence" else "single_pose"
    st.session_state["yoga_mode_key"] = mode_key

    st.markdown("---")
    if mode_key == "single_pose":
        st.header("Pose Selection")
        pose_options = {
            cfg["display_name"]: key
            for key, cfg in YOGA_POSE_CONFIG.items()
        }
        selected_display = st.selectbox(
            "Choose a pose",
            list(pose_options.keys()),
            index=0,
        )
        selected_key = pose_options[selected_display]
        st.session_state["yoga_pose_key"] = selected_key

        cfg = YOGA_POSE_CONFIG[selected_key]
        display_reference_image(cfg)
        if "description" in cfg:
            st.markdown(f"**About:** {cfg['description']}")
            
        st.markdown(f"**Sanskrit:** *{cfg['sanskrit']}*")
        st.markdown(f"**Hold required:** {cfg['min_hold_secs']} seconds")
        st.markdown(f"**Alignment threshold:** {cfg['alignment_threshold']}%")
        st.markdown("---")
        st.info(cfg["cues"]["start"])
    else:
        st.header("Sun Salutation")
        step_idx = st.session_state.get("surya_step_idx", 0)
        step_cfg = SURYA_NAMASKAR_STEPS[step_idx]
        st.subheader(f"Current: {step_cfg['name']}")
        display_reference_image(step_cfg)
        st.markdown(f"**Sanskrit:** *{step_cfg.get('sanskrit', '')}*")
        st.markdown(f"**Mode:** `{step_cfg['mode'].upper()}`")
        st.markdown(f"**Step Duration:** {step_cfg['duration']} seconds")
        if "description" in step_cfg:
            st.markdown(f"**About:** {step_cfg['description']}")
        st.markdown("---")
        st.info(step_cfg["cue"])

    st.markdown("---")
    if st.button("Reset Completions"):
        st.session_state["yoga_completed"] = []
        st.rerun()

# ── Main: WebRTC stream + metrics ─────────────────────────────────────────────
col_cam, col_stats = st.columns([3, 1])

with col_cam:
    ctx = webrtc_streamer(
        key="yoga-trainer",
        video_processor_factory=YogaVideoProcessor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={
            "video": {
                "width":     {"ideal": 640, "max": 800},
                "height":    {"ideal": 480, "max": 600},
                "frameRate": {"ideal": 15,  "max": 15},
            },
            "audio": False,
        },
        async_processing=True,
    )

    # ── Populate Previously Vacant Screen Space Under Live Video ──────────────
    st.markdown("---")
    if mode_key == "single_pose":
        active_key = st.session_state.get("yoga_pose_key", "mountain_pose")
        if ctx.video_processor and ctx.video_processor.mode == "single_pose":
            active_key = ctx.video_processor._yoga_key
        ref_cfg = YOGA_POSE_CONFIG[active_key]
        st.subheader(f"🧘 Target Pose Guide: {ref_cfg['display_name']} ({ref_cfg['sanskrit']})")
        info_col1, info_col2 = st.columns([1, 2])
        with info_col1:
            display_reference_image(ref_cfg, title_prefix="Target: ")
        with info_col2:
            if "description" in ref_cfg:
                st.markdown(f"**About:** {ref_cfg['description']}")
            st.markdown(f"**Target Hold Time:** ⏱️ `{ref_cfg['min_hold_secs']} seconds` | **Required Alignment:** 🎯 `{ref_cfg['alignment_threshold']}%`")
            if "cues" in ref_cfg:
                st.info(f"💡 **Form Cue:** {ref_cfg['cues'].get('start', '')}")
    else:
        step_idx = ctx.video_processor.current_step_idx if ctx.video_processor and ctx.video_processor.mode == "surya_namaskar" else st.session_state.get("surya_step_idx", 0)
        step_cfg = SURYA_NAMASKAR_STEPS[step_idx]
        st.subheader(f"🌞 Step {step_idx+1}: {step_cfg['name']} ({step_cfg.get('sanskrit', '')})")
        info_col1, info_col2 = st.columns([1, 2])
        with info_col1:
            display_reference_image(step_cfg, title_prefix=f"Step {step_idx+1}: ")
        with info_col2:
            st.markdown(f"**Mode:** `{step_cfg['mode'].upper()}` | **Step Duration:** ⏱️ `{step_cfg['duration']}s`")
            if "description" in step_cfg:
                st.markdown(f"**About:** {step_cfg['description']}")
            if "cue" in step_cfg:
                st.info(f"💡 **Guidance:** {step_cfg['cue']}")

if ctx.video_processor:
    if ctx.video_processor.mode != mode_key:
        ctx.video_processor.pending_mode = mode_key
    if mode_key == "single_pose" and ctx.video_processor._yoga_key != selected_key:
        ctx.video_processor.pending_yoga_key = selected_key
    if mode_key == "surya_namaskar":
        st.session_state["surya_step_idx"] = ctx.video_processor.current_step_idx

with col_stats:
    st.subheader("Live Stats")
    st.caption("Real-time alignment metrics and hold progression.")

    if ctx.video_processor:
        proc = ctx.video_processor

        if mode_key == "single_pose":
            cfg = YOGA_POSE_CONFIG[st.session_state.get("yoga_pose_key", "mountain_pose")]
            score = proc.alignment_score
            st.metric("Alignment Score", f"{score:.0f}%")

            hold_s    = proc.hold_duration_secs
            min_hold  = cfg["min_hold_secs"]
            progress  = min(hold_s / max(min_hold, 1.0), 1.0)
            st.progress(float(progress),
                        text=f"Hold: {hold_s:.1f}s / {min_hold}s")

            if proc.active_feedback:
                st.warning(f"🔧 {proc.active_feedback}")
            elif proc.is_holding:
                st.success(cfg["cues"]["hold"])

            if proc.pose_completed:
                st.balloons()
                pose_name = cfg["display_name"]
                if pose_name not in st.session_state["yoga_completed"]:
                    st.session_state["yoga_completed"].append(pose_name)
                st.success(f"✅ {cfg['cues']['complete']}")
        else:
            step_cfg = SURYA_NAMASKAR_STEPS[proc.current_step_idx]
            st.metric("Sequence Progress", f"Step {proc.current_step_idx + 1} / 12")
            st.metric("Alignment Score", f"{proc.alignment_score:.0f}%")

            hold_s = proc.hold_duration_secs
            target_dur = step_cfg["duration"]
            progress = min(hold_s / max(target_dur, 1.0), 1.0)
            st.progress(float(progress), text=f"Step Time: {hold_s:.1f}s / {target_dur}s")

            if proc.active_feedback:
                st.info(f"🧘 {proc.active_feedback}")

            if proc.pose_completed:
                st.balloons()
                st.success("🌞 Surya Namaskar Round Complete!")
                if st.button("Start New Round"):
                    proc._surya_tracker.reset_sequence()
                    st.rerun()

        st.divider()
        st.markdown("**Session Completions**")
        completed = st.session_state["yoga_completed"]
        if completed:
            for name in completed:
                st.markdown(f"- ✅ {name}")
        else:
            st.caption("No poses completed yet this session.")

    else:
        st.info("Start the camera to see live alignment stats.")

# ── Pose reference cards ──────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Pose Library")
cols = st.columns(3)
for i, (key, pose_cfg) in enumerate(YOGA_POSE_CONFIG.items()):
    with cols[i % 3]:
        is_done = pose_cfg["display_name"] in st.session_state["yoga_completed"]
        title   = f"{'✅ ' if is_done else ''}{pose_cfg['display_name']}"
        with st.expander(title):
            st.markdown(f"*{pose_cfg['sanskrit']}*")
            st.markdown(f"- Hold: **{pose_cfg['min_hold_secs']}s**")
            st.markdown(f"- Min alignment: **{pose_cfg['alignment_threshold']}%**")
            st.markdown(f"- Checks: **{len(pose_cfg['landmark_checks'])} joint angles**")
            st.caption(pose_cfg["cues"]["start"])
