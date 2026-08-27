import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ================================================================
#  pages/4_🥗_Nutrition.py  –  Macro / nutrition calculator page
# ================================================================

import streamlit as st
import pandas as pd
import core.data.db as db
from core.utils.auth import require_login
from core.data.nutrition import calculate_bmr, calculate_tdee, calculate_macros

st.set_page_config(page_title="AI Fitness Trainer — Nutrition", page_icon="🥗", layout="wide")

require_login()

st.title("🥗 Nutrition & Macro Calculator")
st.caption(
    "Get personalised daily calorie and macronutrient targets based on your "
    "body stats, activity level, and fitness goal."
)

# ── Disclaimer (always visible, non-dismissible) ────────────────
st.warning(
    "⚠️ **Disclaimer**: These are general estimates based on standard formulas "
    "(Mifflin-St Jeor equation), not personalised medical or dietary advice. "
    "Consult a registered dietitian or doctor for guidance specific to any "
    "medical condition.",
    icon="⚠️",
)

st.markdown("---")

# ── Load user profile ───────────────────────────────────────────
user_id = st.session_state.get("user_id", "")
user = db.get_user_profile(user_id) or {}

# ── Profile form ────────────────────────────────────────────────
st.subheader("Your Profile")

with st.form("profile_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        weight = st.number_input(
            "Weight (kg)", min_value=30.0, max_value=300.0,
            value=float(user.get("weight_kg") or 70.0), step=0.5,
        )
        height = st.number_input(
            "Height (cm)", min_value=100.0, max_value=250.0,
            value=float(user.get("height_cm") or 170.0), step=0.5,
        )

    with col2:
        age = st.number_input(
            "Age", min_value=10, max_value=120,
            value=int(user.get("age") or 25),
        )
        sex = st.selectbox(
            "Sex (for BMR formula)",
            ["male", "female", "other"],
            index=["male", "female", "other"].index(user.get("sex") or "male"),
        )

    with col3:
        activity_level = st.selectbox(
            "Activity Level",
            ["sedentary", "light", "moderate", "active", "very_active"],
            index=["sedentary", "light", "moderate", "active", "very_active"].index(
                user.get("activity_level") or "moderate"
            ),
        )
        fitness_goal = st.selectbox(
            "Fitness Goal",
            ["lose_fat", "maintain", "gain_muscle"],
            index=["lose_fat", "maintain", "gain_muscle"].index(
                user.get("fitness_goal") or "maintain"
            ),
        )

    submitted = st.form_submit_button("Calculate & Save Profile")

if submitted:
    # Save profile to database
    db.update_user_profile(
        st.session_state["user_id"],
        weight_kg=weight,
        height_cm=height,
        age=age,
        sex=sex,
        activity_level=activity_level,
        fitness_goal=fitness_goal,
    )
    st.success("Profile saved!")

    # Calculate
    bmr = calculate_bmr(weight, height, age, sex if sex != "other" else "male")
    tdee = calculate_tdee(bmr, activity_level)
    macros = calculate_macros(tdee, fitness_goal, weight)

    st.markdown("---")
    st.subheader("📊 Your Daily Targets")

    # Summary metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Daily Calories", f"{macros['calories']} kcal")
    col_m2.metric("Protein", f"{macros['protein_g']}g")
    col_m3.metric("Carbs", f"{macros['carbs_g']}g")
    col_m4.metric("Fat", f"{macros['fat_g']}g")

    st.caption(f"BMR: {bmr:.0f} kcal/day · TDEE: {tdee:.0f} kcal/day")

    # Macro breakdown chart (Streamlit native — no matplotlib)
    macro_df = pd.DataFrame({
        "Macro": ["Protein", "Carbs", "Fat"],
        "Grams": [macros["protein_g"], macros["carbs_g"], macros["fat_g"]],
    })
    st.bar_chart(macro_df.set_index("Macro"))

elif user and user.get("weight_kg") and user.get("fitness_goal"):
    # Show existing calculated values if profile is already filled
    bmr = calculate_bmr(
        user["weight_kg"], user["height_cm"], user["age"],
        user["sex"] if user.get("sex") != "other" else "male",
    )
    tdee = calculate_tdee(bmr, user["activity_level"])
    macros = calculate_macros(tdee, user["fitness_goal"], user["weight_kg"])

    st.markdown("---")
    st.subheader("📊 Your Current Daily Targets")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Daily Calories", f"{macros['calories']} kcal")
    col_m2.metric("Protein", f"{macros['protein_g']}g")
    col_m3.metric("Carbs", f"{macros['carbs_g']}g")
    col_m4.metric("Fat", f"{macros['fat_g']}g")

    st.caption(f"BMR: {bmr:.0f} kcal/day · TDEE: {tdee:.0f} kcal/day")

    macro_df = pd.DataFrame({
        "Macro": ["Protein", "Carbs", "Fat"],
        "Grams": [macros["protein_g"], macros["carbs_g"], macros["fat_g"]],
    })
    st.bar_chart(macro_df.set_index("Macro"))
else:
    st.info("Fill in your profile above and click **Calculate & Save Profile** to see your targets.")
