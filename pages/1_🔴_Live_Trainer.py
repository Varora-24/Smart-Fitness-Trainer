import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
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
        # Suppress server-side pyttsx3 voice coaching on Streamlit Community Cloud / headless
        self.pipeline.voice_muted = True
        
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
        annotated = self.pipeline.process_frame(img)
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")


st.title("🏋️ AI Smart Fitness Trainer — Live")
st.caption(
    "Runs entirely in your browser session via WebRTC. Grant camera access "
    "below, then use the sidebar to pick an exercise. Voice coaching is "
    "shown as on-screen captions in this browser version - see the README "
    "for why server-side text-to-speech doesn't carry over the network."
)

col_video, col_controls = st.columns([3, 1])

with col_controls:
    st.subheader("Controls")
    exercise_labels = {cfg["display_name"]: key for key, cfg in EXERCISE_CONFIG.items()}
    chosen_label = st.selectbox("Exercise", list(exercise_labels.keys()))
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
