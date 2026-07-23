import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import streamlit.components.v1 as components
import av
import db
from auth import require_login

from frame_pipeline import FramePipeline
from config import EXERCISE_CONFIG

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
        
        # Drop frames to maintain real-time performance with IMAGE mode
        self.frame_skip = 2 
        self.frame_count = 0
        self.last_out = None
        
        # Init DB session
        try:
            import db
            import streamlit as st
            db.init_db()
            user_id = st.session_state.get("user_id")
            session_id = db.save_session({}, "squats", user_id=user_id)
            self.pipeline.session.session_id = session_id
        except Exception:
            pass

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        
        self.frame_count += 1
        
        # Only process every Nth frame through the ML pipeline to prevent lag
        if self.frame_count % self.frame_skip == 0 or self.last_out is None:
            self.last_out = self.pipeline.process_frame(img)
            
        return av.VideoFrame.from_ndarray(self.last_out, format="bgr24")


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
    
    CAMERA_INSTRUCTIONS = {
        "squats": "📸 **Camera Angle:** Place the camera at hip height, facing you from the side (profile view). Ensure your entire body from head to toe is visible.",
        "pushups": "📸 **Camera Angle:** Place the camera on the floor, facing you from the side. Ensure your entire body from head to toe is visible.",
        "curls": "📸 **Camera Angle:** Place the camera at chest height, facing you from the side (profile view). Ensure your upper body and arms are clearly visible.",
        "lunges": "📸 **Camera Angle:** Place the camera at waist height, facing you from the side (profile view). Ensure your entire body is visible.",
        "shoulder_press": "📸 **Camera Angle:** Place the camera at chest height, facing you from the front or slight angle. Ensure your upper body and arms extended overhead are fully visible."
    }
    
    selected_key = exercise_labels[chosen_label]
    if selected_key in CAMERA_INSTRUCTIONS:
        st.info(CAMERA_INSTRUCTIONS[selected_key])
        
    auto_mode = st.checkbox("Auto-detect exercise", value=False)
    show_debug = st.checkbox("Show debug overlay", value=False)

with col_video:
    ctx = webrtc_streamer(
        key="fitness-trainer-live",
        video_processor_factory=LiveVideoProcessor,
        rtc_configuration=RTC_CONFIGURATION,
        media_stream_constraints={"video": True, "audio": False},
    )

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

# ── Web Speech API TTS (State-based) ────────────────────────
# Check if the WebRTC background thread has queued a new phrase.
# Due to Streamlit's execution model, this will only fire when the UI
# reruns (e.g., via user interaction), but prevents spam via dedup.

if "last_spoken_ts" not in st.session_state:
    st.session_state["last_spoken_ts"] = 0.0

if ctx.video_processor:
    phrase, ts = ctx.video_processor.pipeline.voice.get_browser_phrase()
    if phrase and ts > st.session_state["last_spoken_ts"]:
        st.session_state["last_spoken_ts"] = ts
        safe_phrase = phrase.replace('"', '\\"').replace("\n", " ")
        components.html(
            f"""
            <script>
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance("{safe_phrase}");
                utterance.rate = 1.05;
                window.speechSynthesis.speak(utterance);
            }}
            </script>
            """,
            height=0,
            width=0,
        )
