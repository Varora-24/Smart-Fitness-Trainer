import streamlit as st
from auth import require_login

st.set_page_config(page_title="AI Fitness Trainer — Home", page_icon="🏋️", layout="wide")

require_login()

st.info(
    "🚧 **Active Development** — This project is being actively expanded. "
    "Core features (live trainer, video analysis, nutrition, accounts) are functional; "
    "see the README for what's in progress and what's planned.",
    icon="🚧",
)

st.title("🏋️ AI Smart Fitness Trainer v4 Pro")
st.markdown("---")

st.markdown(
    """
    ### Welcome to the AI Smart Fitness Trainer!
    
    This application uses advanced Computer Vision and Machine Learning to track your exercises in real-time, evaluate your posture, measure range of motion, and score your performance.
    
    #### 🚀 Available Modules
    
    Choose one of the pages from the sidebar or click below to start:
    
    *   **🔴 [Live Trainer](1_🔴_Live_Trainer)**: Real-time pose tracking, rep counting, and form validation using your web camera.
    *   **📊 [History Dashboard](2_📊_History)**: Look at your historical sessions, logs, and calorie trends.
    
    ---
    *Built with ❤️ using Python, Streamlit, MediaPipe, and OpenCV.*
    """
)
