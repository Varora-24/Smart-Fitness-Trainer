import streamlit as st
from core.utils.auth import require_login, logout

st.set_page_config(page_title="AI Fitness Trainer — Home", page_icon="🏋️", layout="wide")

require_login()

st.info(
    "🔥 **Pro Trainer Ready** — All core systems (Live Trainer, Video Analysis, "
    "Nutrition, Supplements, Google OAuth login) are operational!",
    icon="🔥",
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
    #### 💪 Supplement Guide
    Goal-based educational supplement reference  
    (static data, medical disclaimers always shown).
    """)
    st.page_link("pages/5_💊_Supplements.py", label="Open Supplements →", icon="💊")

st.markdown("")

c6, _ = st.columns([1, 2])
with c6:
    st.markdown("""
    #### 🧘 Yoga Coach
    Hold-based yoga pose tracking with real-time alignment scoring,  
    joint-level correction cues, and a 6-pose library.
    """)
    st.page_link("pages/6_🧘_Yoga.py", label="Open Yoga Coach →", icon="🧘")

st.markdown("---")

# ── Coming Soon ─────────────────────────────────────────────
# Kept in sync with README.md #-roadmap section.
# If you add an item here, add it there too (and vice versa).
st.subheader("🔮 Coming Soon")
st.caption(
    "These features are planned but not yet built. "
    "The app is actively developed — check back regularly."
)
with st.container(border=True):
    cols_cs = st.columns(3)
    with cols_cs[0]:
        st.markdown("**👥 Google Sign-In**")
        st.caption("One-click login via Google OAuth — no password required.")
    with cols_cs[1]:
        st.markdown("**📱 Multi-Person Tracking**")
        st.caption("Independent pose instances for each detected person in the frame.")
    with cols_cs[2]:
        st.markdown("**📱 Mobile-Responsive Layout**")
        st.caption("Optimised UI for phones and tablets.")
    cols_cs2 = st.columns(3)
    with cols_cs2[0]:
        st.markdown("**🏗️ Custom Exercise Builder**")
        st.caption("Record baseline poses to define entirely new exercises.")
    with cols_cs2[1]:
        st.markdown("**⌚ Integration with Wearables**")
        st.caption("Sync heart rate and metabolic data from fitness devices.")
    with cols_cs2[2]:
        st.markdown("**🤖 AI Workout Planner**")
        st.caption("Personalised weekly training plans generated from your history.")

st.markdown("---")
st.caption("Built with ❤️ using Python, Streamlit, MediaPipe, OpenCV and Supabase.")
