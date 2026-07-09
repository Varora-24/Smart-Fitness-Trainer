# ================================================================
#  pages/5_💊_Supplements.py  –  Educational supplement info page
# ================================================================

import streamlit as st
import db
from auth import require_login
from supplement_data import SUPPLEMENT_INFO, MANDATORY_DISCLAIMER

st.set_page_config(
    page_title="AI Fitness Trainer — Supplements",
    page_icon="💊",
    layout="wide",
)

require_login()

st.title("💊 Supplement Information")
st.caption(
    "Goal-based educational information about commonly discussed supplements. "
    "This is NOT personalised medical advice — see disclaimer below."
)

# ── Mandatory disclaimer — always shown, prominently ─────────────
st.error(f"⚠️ {MANDATORY_DISCLAIMER}", icon="⚠️")

st.markdown("---")

# ── Get the user's fitness goal ─────────────────────────────────
user = db.get_user_by_email(st.session_state["email"])
user_goal = user.get("fitness_goal") if user else None

# Map DB goal keys to display labels
GOAL_LABELS = {
    "lose_fat": "🔥 Lose Fat",
    "maintain": "⚖️ Maintain",
    "gain_muscle": "💪 Gain Muscle",
    "endurance": "🏃 Endurance",
    "general_health": "🌿 General Health",
}

available_goals = list(SUPPLEMENT_INFO.keys())
display_options = [GOAL_LABELS.get(g, g) for g in available_goals]

# Pre-select user's goal if they have one set
default_idx = 0
if user_goal and user_goal in available_goals:
    default_idx = available_goals.index(user_goal)

selected_label = st.selectbox("Select your goal:", display_options, index=default_idx)
selected_goal = available_goals[display_options.index(selected_label)]

# ── Display supplement list ─────────────────────────────────────
st.subheader(f"Supplements for: {selected_label}")

supplements = SUPPLEMENT_INFO.get(selected_goal, [])

if not supplements:
    st.info("No supplement information available for this goal yet.")
else:
    for i, supp in enumerate(supplements, 1):
        with st.container():
            st.markdown(f"### {i}. {supp['name']}")
            st.markdown(f"_{supp['note']}_")
            st.markdown("")

# ── Repeat disclaimer at bottom ─────────────────────────────────
st.markdown("---")
st.warning(f"📋 {MANDATORY_DISCLAIMER}", icon="📋")
