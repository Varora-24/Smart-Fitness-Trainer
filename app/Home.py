import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.utils.auth import require_login, logout

st.set_page_config(page_title="AI Fitness Trainer", layout="wide")

def dashboard():
    require_login()

    from core.utils.icons import ui_alert, get_icon_html
    
    ui_alert(
        "**Pro Trainer Ready** — All core systems (Live Trainer, Video Analysis, "
        "Nutrition, Supplements, Google OAuth login) are operational!",
        type="info"
    )

    # ── Header ───────────────────────────────────────────────────────
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.markdown(f"<h1>{get_icon_html('dumbbell', size=36)} AI Smart Fitness Trainer v4 Pro</h1>", unsafe_allow_html=True)
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out", use_container_width=True):
            logout()

    st.markdown(f"Welcome back, **{st.session_state.get('email', 'Athlete')}** 👋")
    st.markdown("---")

    # ── Feature cards ────────────────────────────────────────────────
    st.markdown(f"<h3>{get_icon_html('blocks', size=24)} Available Modules</h3>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<h4>{get_icon_html('activity', size=20)} Live Trainer</h4>", unsafe_allow_html=True)
        st.markdown("Real-time pose tracking, rep counting, and form scoring via your webcam — powered by MediaPipe + WebRTC.")
        st.page_link("pages/1_🔴_Live_Trainer.py", label="Open Live Trainer →")

    with c2:
        st.markdown(f"<h4>{get_icon_html('history', size=20)} Workout History</h4>", unsafe_allow_html=True)
        st.markdown("Browse all past sessions with charts for form score trends, calorie totals, rep quality, and exercise distribution.")
        st.page_link("pages/2_📊_History.py", label="Open History →")

    with c3:
        st.markdown(f"<h4>{get_icon_html('film', size=20)} Video Analysis</h4>", unsafe_allow_html=True)
        st.markdown("Upload any workout clip and get a full AI breakdown: good/bad reps, calories, per-rep form scores, annotated video.")
        st.page_link("pages/3_📹_Video_Analysis.py", label="Open Video Analysis →")

    st.markdown("")

    c4, c5 = st.columns(2)
    with c4:
        st.markdown(f"<h4>{get_icon_html('utensils', size=20)} Nutrition Calculator</h4>", unsafe_allow_html=True)
        st.markdown("Personalised daily calorie & macro targets (protein, carbs, fat) using the Mifflin-St Jeor equation based on your profile.")
        st.page_link("pages/4_🥗_Nutrition.py", label="Open Nutrition →")

    with c5:
        st.markdown(f"<h4>{get_icon_html('pill', size=20)} Supplement Guide</h4>", unsafe_allow_html=True)
        st.markdown("Goal-based educational supplement reference (static data, medical disclaimers always shown).")
        st.page_link("pages/5_💊_Supplements.py", label="Open Supplements →")

    st.markdown("")

    c6, _ = st.columns([1, 2])
    with c6:
        st.markdown(f"<h4>{get_icon_html('person-standing', size=20)} Yoga Coach</h4>", unsafe_allow_html=True)
        st.markdown("Hold-based yoga pose tracking with real-time alignment scoring, joint-level correction cues, and a 6-pose library.")
        st.page_link("pages/6_🧘_Yoga.py", label="Open Yoga Coach →")

    st.markdown("---")

    # ── Coming Soon ─────────────────────────────────────────────
    st.markdown(f"<h3>{get_icon_html('sparkles', size=24)} Coming Soon</h3>", unsafe_allow_html=True)
    st.caption("These features are planned but not yet built. The app is actively developed — check back regularly.")
    
    with st.container(border=True):
        cols_cs = st.columns(3)
        with cols_cs[0]:
            st.markdown(f"**{get_icon_html('users', size=16)} Multi-Person Tracking**", unsafe_allow_html=True)
            st.caption("Independent pose instances for each detected person in the frame.")
        with cols_cs[1]:
            st.markdown(f"**{get_icon_html('smartphone', size=16)} Mobile-Responsive Layout**", unsafe_allow_html=True)
            st.caption("Optimised UI for phones and tablets.")
        with cols_cs[2]:
            st.markdown(f"**{get_icon_html('hammer', size=16)} Custom Exercise Builder**", unsafe_allow_html=True)
            st.caption("Record baseline poses to define entirely new exercises.")
        cols_cs2 = st.columns(3)
        with cols_cs2[0]:
            st.markdown(f"**{get_icon_html('watch', size=16)} Integration with Wearables**", unsafe_allow_html=True)
            st.caption("Sync heart rate and metabolic data from fitness devices.")
        with cols_cs2[1]:
            st.markdown(f"**{get_icon_html('bot', size=16)} AI Workout Planner**", unsafe_allow_html=True)
            st.caption("Personalised weekly training plans generated from your history.")

    st.markdown("---")
    st.caption("Built with ❤️ using Python, Streamlit, MediaPipe, OpenCV and Supabase.")

pg = st.navigation([
    st.Page(dashboard, title="Home", icon=":material/home:", default=True),
    st.Page("pages/1_🔴_Live_Trainer.py", title="Live Trainer", icon=":material/videocam:"),
    st.Page("pages/2_📊_History.py", title="Workout History", icon=":material/history:"),
    st.Page("pages/3_📹_Video_Analysis.py", title="Video Analysis", icon=":material/movie:"),
    st.Page("pages/4_🥗_Nutrition.py", title="Nutrition", icon=":material/restaurant:"),
    st.Page("pages/5_💊_Supplements.py", title="Supplements", icon=":material/medication:"),
    st.Page("pages/6_🧘_Yoga.py", title="Yoga Coach", icon=":material/self_improvement:")
])
pg.run()
