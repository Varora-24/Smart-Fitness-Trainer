import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.utils.auth import require_login, logout

st.set_page_config(page_title="AI Fitness Trainer â€” Home", page_icon="ðŸ‹ï¸", layout="wide")

require_login()

st.info(
    "ðŸ”¥ **Pro Trainer Ready** â€” All core systems (Live Trainer, Video Analysis, "
    "Nutrition, Supplements, Google OAuth login) are operational!",
    icon="ðŸ”¥",
)

# â”€â”€ Header â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
col_title, col_logout = st.columns([4, 1])
with col_title:
    st.title("ðŸ‹ï¸ AI Smart Fitness Trainer v4 Pro")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ðŸšª Log Out", use_container_width=True):
        logout()

st.markdown(f"Welcome back, **{st.session_state.get('email', 'Athlete')}** ðŸ‘‹")
st.markdown("---")

# â”€â”€ Feature cards â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.subheader("ðŸš€ Available Modules")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    #### ðŸ”´ Live Trainer
    Real-time pose tracking, rep counting, and form scoring  
    via your webcam â€” powered by MediaPipe + WebRTC.
    """)
    st.page_link("pages/1_ðŸ”´_Live_Trainer.py", label="Open Live Trainer â†’", icon="ðŸ”´")

with c2:
    st.markdown("""
    #### ðŸ“Š Workout History
    Browse all past sessions with charts for form score trends,  
    calorie totals, rep quality, and exercise distribution.
    """)
    st.page_link("pages/2_ðŸ“Š_History.py", label="Open History â†’", icon="ðŸ“Š")

with c3:
    st.markdown("""
    #### ðŸ“¹ Video Analysis
    Upload any workout clip and get a full AI breakdown:  
    good/bad reps, calories, per-rep form scores, annotated video.
    """)
    st.page_link("pages/3_ðŸ“¹_Video_Analysis.py", label="Open Video Analysis â†’", icon="ðŸ“¹")

st.markdown("")

c4, c5 = st.columns(2)
with c4:
    st.markdown("""
    #### ðŸ¥— Nutrition Calculator
    Personalised daily calorie & macro targets (protein, carbs, fat)  
    using the Mifflin-St Jeor equation based on your profile.
    """)
    st.page_link("pages/4_ðŸ¥—_Nutrition.py", label="Open Nutrition â†’", icon="ðŸ¥—")

with c5:
    st.markdown("""
    #### ðŸ’ª Supplement Guide
    Goal-based educational supplement reference  
    (static data, medical disclaimers always shown).
    """)
    st.page_link("pages/5_ðŸ’Š_Supplements.py", label="Open Supplements â†’", icon="ðŸ’Š")

st.markdown("")

c6, _ = st.columns([1, 2])
with c6:
    st.markdown("""
    #### ðŸ§˜ Yoga Coach
    Hold-based yoga pose tracking with real-time alignment scoring,  
    joint-level correction cues, and a 6-pose library.
    """)
    st.page_link("pages/6_ðŸ§˜_Yoga.py", label="Open Yoga Coach â†’", icon="ðŸ§˜")

st.markdown("---")

# â”€â”€ Coming Soon â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Kept in sync with README.md #-roadmap section.
# If you add an item here, add it there too (and vice versa).
st.subheader("ðŸ”® Coming Soon")
st.caption(
    "These features are planned but not yet built. "
    "The app is actively developed â€” check back regularly."
)
with st.container(border=True):
    cols_cs = st.columns(3)
    with cols_cs[0]:
        st.markdown("**ðŸ‘¥ Multi-Person Tracking**")
        st.caption("Independent pose instances for each detected person in the frame.")
    with cols_cs[1]:
        st.markdown("**ðŸ“± Mobile-Responsive Layout**")
        st.caption("Optimised UI for phones and tablets.")
    with cols_cs[2]:
        st.markdown("**ðŸ—ï¸ Custom Exercise Builder**")
        st.caption("Record baseline poses to define entirely new exercises.")
    cols_cs2 = st.columns(3)
    with cols_cs2[0]:
        st.markdown("**âŒš Integration with Wearables**")
        st.caption("Sync heart rate and metabolic data from fitness devices.")
    with cols_cs2[1]:
        st.markdown("**ðŸ¤– AI Workout Planner**")
        st.caption("Personalised weekly training plans generated from your history.")

st.markdown("---")
st.caption("Built with â¤ï¸ using Python, Streamlit, MediaPipe, OpenCV and Supabase.")
