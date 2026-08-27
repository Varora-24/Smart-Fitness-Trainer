import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ================================================================
#  pages/5_ðŸ’Š_Supplements.py  â€“  Educational supplement info page
# ================================================================

import streamlit as st
import core.data.db as db
from core.utils.auth import require_login
from core.data.supplement_data import SUPPLEMENT_INFO, MANDATORY_DISCLAIMER

st.set_page_config(
    page_title="AI Fitness Trainer â€” Supplements",
    page_icon="ðŸ’Š",
    layout="wide",
)

require_login()

st.title("ðŸ’Š Supplement Information")
st.caption(
    "Goal-based educational information about commonly discussed supplements. "
    "This is NOT personalised medical advice â€” see disclaimer below."
)

# â”€â”€ Mandatory disclaimer â€” always shown, prominently â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.error(f"âš ï¸ {MANDATORY_DISCLAIMER}", icon="âš ï¸")

st.markdown("---")

# â”€â”€ Get the user's fitness goal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
user_id = st.session_state.get("user_id", "")
user = db.get_user_profile(user_id) or {}
user_goal = user.get("fitness_goal")

# Map DB goal keys to display labels
GOAL_LABELS = {
    "lose_fat": "ðŸ”¥ Lose Fat",
    "maintain": "âš–ï¸ Maintain",
    "gain_muscle": "ðŸ’ª Gain Muscle",
    "endurance": "ðŸƒ Endurance",
    "general_health": "ðŸŒ¿ General Health",
}

available_goals = list(SUPPLEMENT_INFO.keys())
display_options = [GOAL_LABELS.get(g, g) for g in available_goals]

# Pre-select user's goal if they have one set
default_idx = 0
if user_goal and user_goal in available_goals:
    default_idx = available_goals.index(user_goal)

selected_label = st.selectbox("Select your goal:", display_options, index=default_idx)
selected_goal = available_goals[display_options.index(selected_label)]

# â”€â”€ Display supplement list â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

# â”€â”€ Repeat disclaimer at bottom â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.markdown("---")
st.warning(f"ðŸ“‹ {MANDATORY_DISCLAIMER}", icon="ðŸ“‹")
