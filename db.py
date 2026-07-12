# ================================================================
#  db.py  –  Supabase database layer for workout history
# ================================================================

import logging
from datetime import datetime
import streamlit as st
import auth

logger = logging.getLogger("db")


def _get_client():
    """Return the authenticated client for the current user."""
    return auth.get_authenticated_client()


def init_db() -> None:
    """Initialize the database schema. No-op for Supabase as schema is managed centrally."""
    pass


def get_user_profile(user_id: str) -> dict | None:
    """Retrieve the current user's profile from the profiles table."""
    client = _get_client()
    try:
        res = client.table("profiles").select("*").eq("id", user_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error("Could not reach the database right now. Please check your connection.")
        logger.error(f"Supabase query failed: {e}")
        return None


def update_user_profile(user_id: str, **fields: object) -> None:
    """
    Update profile fields for a user.

    Only the following columns are allowed:
    display_name, weight_kg, height_cm, age, sex, activity_level, fitness_goal.
    """
    allowed = {
        "display_name", "weight_kg", "height_cm", "age",
        "sex", "activity_level", "fitness_goal",
    }
    to_update = {k: v for k, v in fields.items() if k in allowed}
    if not to_update:
        return

    to_update["id"] = user_id
    client = _get_client()
    try:
        client.table("profiles").upsert(to_update).execute()
    except Exception as e:
        st.error("Could not reach the database right now. Your profile may not have been updated.")
        logger.error(f"Supabase upsert failed: {e}")


# ── Session / rep functions ──────────────────────────────────────

def save_session(summary_dict: dict, exercise: str, user_id: str | None = None) -> int:
    """
    Save a workout session summary to the sessions table.
    """
    client = _get_client()
    now_str = datetime.now().isoformat()
    try:
        res = client.table("sessions").insert({
            "user_id": user_id,
            "exercise": exercise,
            "total_reps": summary_dict.get("total_reps", 0),
            "clean_reps": summary_dict.get("clean_reps", 0),
            "bad_reps": summary_dict.get("bad_reps", 0),
            "calories": summary_dict.get("calories", 0.0),
            "duration_secs": summary_dict.get("duration_secs", 0.0),
            "avg_rep_score": summary_dict.get("avg_rep_score", 0.0),
            "started_at": now_str
        }).execute()
        if res.data:
            return res.data[0]["id"]
    except Exception as e:
        st.error("Could not reach the database right now. Your workout data may not have been saved.")
        logger.error(f"Supabase session insert failed: {e}")
    return 0


def save_all_reps(session_id: int, feature_rows: list) -> None:
    """
    Bulk save a list of reps for a given session.
    """
    if not feature_rows or not session_id:
        return
    
    client = _get_client()
    now_str = datetime.now().isoformat()
    reps_data = []
    
    for row in feature_rows:
        reps_data.append({
            "session_id": session_id,
            "exercise": row.get("exercise", "unknown"),
            "symmetry": row.get("symmetry", 0.0),
            "range_of_motion": row.get("range_of_motion", 0.0),
            "posture": row.get("posture", 0.0),
            "control": row.get("control", 0.0),
            "rep_score": row.get("rep_score", 0.0),
            "rep_label": row.get("rep_label", "bad_rep"),
            "created_at": now_str
        })
        
    try:
        client.table("reps").insert(reps_data).execute()
    except Exception as e:
        logger.error(f"Supabase rep bulk insert failed: {e}")


def get_history(exercise: str | None = None, limit: int = 50, user_id: str | None = None) -> list:
    """
    Retrieve session history, optionally filtered by exercise.
    RLS ensures users only see their own sessions.
    """
    client = _get_client()
    query = client.table("sessions").select("*")
    if exercise:
        query = query.eq("exercise", exercise)
    query = query.order("started_at", desc=True).limit(limit)
    
    try:
        res = query.execute()
        # Rename started_at to date for backward compatibility with existing UI
        rows = []
        for r in res.data:
            r["date"] = r.pop("started_at", "")
            rows.append(r)
        return rows
    except Exception as e:
        st.error("Could not fetch history right now.")
        logger.error(f"Supabase history fetch failed: {e}")
        return []


def get_reps_for_user(user_id: str, limit: int = 200) -> list:
    """
    Retrieve rep history for the current user.
    RLS inherently filters by user via the reps -> sessions policy.
    """
    client = _get_client()
    try:
        # Note: in Supabase, we don't strictly need to join just to filter,
        # because the policy prevents seeing other users' reps anyway.
        res = client.table("reps").select("*").order("created_at", desc=True).limit(limit).execute()
        # Rename created_at to timestamp for backward compatibility
        rows = []
        for r in res.data:
            r["timestamp"] = r.pop("created_at", "")
            rows.append(r)
        return rows
    except Exception as e:
        st.error("Could not fetch reps right now.")
        logger.error(f"Supabase reps fetch failed: {e}")
        return []
