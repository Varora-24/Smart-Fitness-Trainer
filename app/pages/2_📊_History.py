import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ================================================================
#  pages/2_📊_History.py  –  Streamlit workout analytics dashboard
# ================================================================

import streamlit as st
import pandas as pd
import os
import json
import core.data.db as db
from core.utils.auth import require_login

# ── Page Configuration ──────────────────────────────────────────
st.set_page_config(
    page_title="AI Smart Fitness Trainer Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

require_login()

from core.utils.icons import ui_alert, get_icon_html  # noqa: E402

# Custom CSS for premium aesthetics
st.markdown("""
    <style>
    .main {
        background-color: #0f111a;
        color: #ffffff;
    }
    .metric-card {
        background-color: #1a1c24;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #2a2d3d;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #00ffcc;
    }
    .metric-label {
        font-size: 1rem;
        color: #8c92a6;
    }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "workout_history.db"

# ── Data Loading Helpers ────────────────────────────────────────
def load_db_data(user_id: str):
    """Load sessions and reps for the currently logged-in user."""
    try:
        sessions = db.get_history(user_id=user_id, limit=200)
        reps = db.get_reps_for_user(user_id=user_id, limit=2000)
        
        df_sessions = pd.DataFrame(sessions)
        df_reps = pd.DataFrame(reps)
        return df_sessions, df_reps
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ── Title Header ────────────────────────────────────────────────
st.markdown(f"<h1>{get_icon_html('dumbbell', size=36)} AI Smart Fitness Trainer - Workout Dashboard</h1>", unsafe_allow_html=True)
st.write("Track your exercise progress, form quality, and training history in real-time.")
st.markdown("---")

# ── Load Data (filtered by current user) ────────────────────────
current_user_id = st.session_state["user_id"]
df_sessions, df_reps = load_db_data(current_user_id)

# ── Live Session View / Last Session tab ────────────────────────
tab_live, tab_history = st.tabs(["Live Session Summary", "Historical Trends"])

with tab_live:
    st.subheader("Last Session Overview")

    if os.path.exists("last_session.json"):
        try:
            with open("last_session.json", "r") as fh:
                last_session = json.load(fh)

            # Render Metrics Cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{last_session.get('exercise', 'N/A')}</div>
                        <div class="metric-label">Last Exercise</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{last_session.get('total_reps', 0)}</div>
                        <div class="metric-label">Total Reps</div>
                    </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{last_session.get('clean_reps', 0)} / <span style="color:#ff4d4d">{last_session.get('bad_reps', 0)}</span></div>
                        <div class="metric-label">Clean / Bad Reps</div>
                    </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{last_session.get('calories', 0.0):.2f} kcal</div>
                        <div class="metric-label">Calories Burned</div>
                    </div>
                """, unsafe_allow_html=True)

            st.write("")
            col_l1, col_l2, col_l3 = st.columns(3)
            with col_l1:
                st.metric("Avg Rep Score", f"{last_session.get('avg_rep_score', 0.0):.1f} / 100")
            with col_l2:
                st.metric("Avg Symmetry", f"{last_session.get('avg_symmetry', 0.0):.1f}%")
            with col_l3:
                st.metric("Reps Per Minute (RPM)", f"{last_session.get('reps_per_min', 0.0):.1f}")
        except Exception as e:
            ui_alert(f"Could not load last session details: {e}", type="warning")
    else:
        ui_alert("No live session data found. Complete a workout to see summary here!", type="info")

with tab_history:
    st.subheader("Workout Performance History")

    if df_sessions.empty:
        ui_alert("No historical sessions found. Run the trainer to start collecting data!", type="info")
    else:
        # Prepare data fields
        df_sessions['date'] = pd.to_datetime(df_sessions['date'])
        df_sessions['date_str'] = df_sessions['date'].dt.strftime('%m-%d %H:%M')

        # Summary metrics
        total_sessions = len(df_sessions)
        total_reps_all = df_sessions['total_reps'].sum()
        total_calories_all = df_sessions['calories'].sum()
        avg_score_all = df_sessions['avg_rep_score'].mean()

        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        col_h1.metric("Total Sessions", total_sessions)
        col_h2.metric("Accumulated Reps", total_reps_all)
        col_h3.metric("Total Calories", f"{total_calories_all:.1f} kcal")
        col_h4.metric("Lifetime Avg Form Score", f"{avg_score_all:.1f}%")

        st.write("")

        # Visual charts
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown(f"**{get_icon_html('chart-bar', size=18)} Reps Per Session Over Time**", unsafe_allow_html=True)
            chart_reps = df_sessions.set_index('date_str')[['total_reps', 'clean_reps']]
            st.bar_chart(chart_reps)

        with col_chart2:
            st.markdown(f"**{get_icon_html('flame', size=18)} Calories Burned Per Session**", unsafe_allow_html=True)
            chart_calories = df_sessions.set_index('date_str')[['calories']]
            st.line_chart(chart_calories)

        st.write("")
        col_chart3, col_chart4 = st.columns(2)

        with col_chart3:
            st.markdown(f"**{get_icon_html('target', size=18)} Form Quality Score by Session**", unsafe_allow_html=True)
            chart_scores = df_sessions.set_index('date_str')[['avg_rep_score']]
            st.line_chart(chart_scores)

        with col_chart4:
            st.markdown(f"**{get_icon_html('activity', size=18)} Activity Breakdown by Exercise Type**", unsafe_allow_html=True)
            ex_breakdown = df_sessions.groupby('exercise')['total_reps'].sum().reset_index()
            st.bar_chart(ex_breakdown.set_index('exercise'))

        # Show raw database tables
        st.write("")
        st.markdown(f"**{get_icon_html('history', size=18)} Recent Workout Logs**", unsafe_allow_html=True)
        st.dataframe(
            df_sessions.drop(columns=['date_str']).sort_values('date', ascending=False),
            use_container_width=True,
        )
