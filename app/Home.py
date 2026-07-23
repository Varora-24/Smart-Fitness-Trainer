import streamlit as st
from core.utils.auth import require_login, logout

st.set_page_config(page_title="AI Fitness Trainer — Home", page_icon="🏋️", layout="wide")

require_login()

st.info(
    "🚧 **Active Development** — Core features (live trainer, video analysis, "
    "nutrition, supplements, accounts) are functional. More coming soon!",
    icon="🚧",
)

# ── Header ───────────────────────────────────────────────────────
col_title, col_logout = st.columns([4, 1])
with col_title:
    st.title("🏋️ AI Smart Fitness Trainer v4 Pro")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Log Out", use_container_width=True):
        logout()

st.markdown(f"Welcome back, **{st.session_state.get('email', 'Athlete')}** 👋")
st.markdown("---")

# ── Feature cards ────────────────────────────────────────────────
st.subheader("🚀 Available Modules")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    #### 🔴 Live Trainer
    Real-time pose tracking, rep counting, and form scoring  
    via your webcam — powered by MediaPipe + WebRTC.
    """)
    st.page_link("pages/1_🔴_Live_Trainer.py", label="Open Live Trainer →", icon="🔴")

with c2:
    st.markdown("""
    #### 📊 Workout History
    Browse all past sessions with charts for form score trends,  
    calorie totals, rep quality, and exercise distribution.
    """)
    st.page_link("pages/2_📊_History.py", label="Open History →", icon="📊")

with c3:
    st.markdown("""
    #### 📹 Video Analysis
    Upload any workout clip and get a full AI breakdown:  
    good/bad reps, calories, per-rep form scores, annotated video.
    """)
    st.page_link("pages/3_📹_Video_Analysis.py", label="Open Video Analysis →", icon="📹")

st.markdown("")

c4, c5 = st.columns(2)
with c4:
    st.markdown("""
    #### 🥗 Nutrition Calculator
    Personalised daily calorie & macro targets (protein, carbs, fat)  
    using the Mifflin-St Jeor equation based on your profile.
    """)
    st.page_link("pages/4_🥗_Nutrition.py", label="Open Nutrition →", icon="🥗")

with c5:
    st.markdown("""
    #### 💊 Supplement Guide
    Goal-based educational supplement reference  
    (static data, medical disclaimers always shown).
    """)
    st.page_link("pages/5_💊_Supplements.py", label="Open Supplements →", icon="💊")

st.markdown("---")
st.caption("Built with ❤️ using Python, Streamlit, MediaPipe, OpenCV and Supabase.")
