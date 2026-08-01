import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import streamlit.components.v1 as components
import av
import core.data.db as db
from core.utils.auth import require_login

from core.tracking.frame_pipeline import FramePipeline
from core.utils.config import EXERCISE_CONFIG, display_reference_image

st.set_page_config(page_title="AI Fitness Trainer — Live", page_icon="🏋️", layout="wide")

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
        
        # Frame-skip: run MediaPipe inference every N frames for stability.
        # recv() still returns a rendered frame every call (full ~30 fps video)
        # by holding the last annotated output between inference frames.
        # Before: inference on every frame  → ~30 fps inference load
        # After:  inference every 4th frame → ~4 fps inference (at 15fps source), 15 fps render
        self._skip_n     = 4      # run inference on frame 0, 4, 8, …
        self._frame_idx  = 0      # rolling counter (reset mod _skip_n)
        self._last_out   = None   # last annotated ndarray to hold & return
        
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

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        orig_h, orig_w = img.shape[:2]

        # Run MediaPipe inference only on every _skip_n-th frame.
        # On skipped frames return the previous annotated output so the
        # browser stream stays smooth at full camera FPS (~30 fps) while
        # inference load drops to ~10 fps — the accuracy-for-stability
        # tradeoff requested for Live Trainer only.
        if self._frame_idx % self._skip_n == 0 or self._last_out is None:
            self._last_out = self.pipeline.process_frame(img)

        self._frame_idx = (self._frame_idx + 1) % self._skip_n
        out = self._last_out.copy()
        if out.shape[:2] != (orig_h, orig_w):
            import cv2
            out = cv2.resize(out, (orig_w, orig_h))
        return av.VideoFrame.from_ndarray(out, format="bgr24")


st.title("🏋️ AI Smart Fitness Trainer — Live")
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
    st.caption("ℹ️ Adjust exercise selection and overlay settings during live tracking.")

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
    )

    # ── Populate Previously Vacant Screen Space Under Live Video ──────────────
    st.markdown("---")
    st.subheader(f"🎯 Exercise Form & Guidance: {cfg['display_name']}")
    
    CAMERA_INSTRUCTIONS = {
        "squats": "📸 **Camera Angle:** Place the camera at hip height, facing you from the side (profile view). Ensure your entire body from head to toe is visible.",
        "pushups": "📸 **Camera Angle:** Place the camera on the floor, facing you from the side. Ensure your entire body from head to toe is visible.",
        "curls": "📸 **Camera Angle:** Place the camera at chest height, facing you from the side (profile view). Ensure your upper body and arms are clearly visible.",
        "lunges": "📸 **Camera Angle:** Place the camera at waist height, facing you from the side (profile view). Ensure your entire body is visible.",
        "shoulder_press": "📸 **Camera Angle:** Place the camera at chest height, facing you from the front or slight angle. Ensure your upper body and arms extended overhead are fully visible."
    }

    info_col1, info_col2 = st.columns([1, 2])
    with info_col1:
        display_reference_image(cfg)
    with info_col2:
        if "description" in cfg:
            st.markdown(f"**About:** {cfg['description']}")
        if "kcal_per_rep" in cfg:
            st.markdown(f"**Est. Burn:** 🔥 `{cfg['kcal_per_rep']} kcal / rep`")
        if "angle_range" in cfg:
            lo, hi = cfg['angle_range']
            st.markdown(f"**Target Range of Motion:** 📐 `{lo}° – {hi}°`")
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

        st.subheader("📊 Session Summary")
        st.json(s)

# ── Web Speech API TTS (JS polling bridge) ──────────────────
# Architecture:
#   1. A persistent JS poller is injected once on page load (hidden iframe).
#      It polls window.sessionStorage["tts_phrase"] + "tts_ts" every 500ms.
#      When a new (phrase, ts) pair appears it speaks via Web Speech API.
#   2. When VoiceCoach queues a new phrase (from the WebRTC thread),
#      the Python side writes it to sessionStorage via a zero-height component.
#      This fires on the next Streamlit rerun which happens naturally due to
#      WebRTC state updates.
#   This fires without requiring explicit user interaction.

if "_tts_bridge_injected" not in st.session_state:
    st.session_state["_tts_bridge_injected"] = True
    components.html(
        """
        <script>
        (function() {
            // Persistent TTS poller — survives Streamlit partial rerenders
            if (window._ttsBridgeRunning) return;
            window._ttsBridgeRunning = true;
            window._lastTtsTs = 0;

            function speak(phrase) {
                if (!('speechSynthesis' in window)) return;
                // Cancel any ongoing speech first
                window.speechSynthesis.cancel();
                var utterance = new SpeechSynthesisUtterance(phrase);
                utterance.rate = 1.05;
                utterance.volume = 1.0;
                window.speechSynthesis.speak(utterance);
            }

            setInterval(function() {
                try {
                    var phrase = window.sessionStorage.getItem('tts_phrase');
                    var ts     = parseFloat(window.sessionStorage.getItem('tts_ts') || '0');
                    if (phrase && ts > window._lastTtsTs) {
                        window._lastTtsTs = ts;
                        speak(phrase);
                    }
                } catch(e) {}
            }, 500);
        })();
        </script>
        """,
        height=0,
        width=0,
    )

if "last_spoken_ts" not in st.session_state:
    st.session_state["last_spoken_ts"] = 0.0

if ctx.video_processor:
    phrase, ts = ctx.video_processor.pipeline.voice.get_browser_phrase()
    if phrase and ts > st.session_state["last_spoken_ts"]:
        st.session_state["last_spoken_ts"] = ts
        # Escape phrase for JS string safety
        safe_phrase = phrase.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
        # Write to sessionStorage so the persistent poller above picks it up
        components.html(
            f"""
            <script>
            try {{
                window.parent.sessionStorage.setItem('tts_phrase', "{safe_phrase}");
                window.parent.sessionStorage.setItem('tts_ts', '{ts}');
            }} catch(e) {{
                // Fallback: speak directly in this iframe context
                if ('speechSynthesis' in window.parent) {{
                    var u = new window.parent.SpeechSynthesisUtterance("{safe_phrase}");
                    u.rate = 1.05;
                    window.parent.speechSynthesis.speak(u);
                }}
            }}
            </script>
            """,
            height=0,
            width=0,
        )
