# ================================================================
#  db.py  –  Supabase database layer for workout history
# ================================================================

import logging
from datetime import datetime
import threading
import streamlit as st
import core.utils.auth as auth

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
    Create a workout session and return its ID.
    """
    client = _get_client()
    now_str = datetime.now().isoformat()
    try:
        res = client.table("sessions").insert({
            "user_id": user_id,
            "exercise": exercise,
            "total_reps": 0,
            "clean_reps": 0,
            "bad_reps": 0,
            "calories": 0.0,
            "duration_secs": 0.0,
            "avg_rep_score": 0.0,
            "started_at": now_str
        }).execute()
        if res.data:
            return res.data[0]["id"]
    except Exception as e:
        st.error("Could not reach the database right now. Your workout data may not have been saved.")
        logger.error(f"Supabase session insert failed: {e}")
    return 0


def update_session(session_id: int, summary_dict: dict) -> None:
    """
    Update a workout session with final metrics.
    """
    if not session_id:
        return
    client = _get_client()
    try:
        client.table("sessions").update({
            "total_reps": summary_dict.get("total_reps", 0),
            "clean_reps": summary_dict.get("clean_reps", 0),
            "bad_reps": summary_dict.get("bad_reps", 0),
            "calories": summary_dict.get("calories", 0.0),
            "duration_secs": summary_dict.get("duration_secs", 0.0),
            "avg_rep_score": summary_dict.get("avg_rep_score", 0.0)
        }).eq("id", session_id).execute()
    except Exception as e:
        logger.error(f"Supabase session update failed: {e}")

def _save_rep_background(client, rep_data):
    try:
        client.table("reps").insert(rep_data).execute()
    except Exception as e:
        logger.error(f"Supabase rep insert failed (background): {e}")

def save_rep(session_id: int, row: dict) -> None:
    """
    Save a single rep incrementally (non-blocking).
    """
    if not session_id or not row:
        return
    
    # Get client in the calling thread (where st.session_state is available)
    try:
        client = _get_client()
    except Exception as e:
        logger.warning(f"Could not get Supabase client in save_rep (thread context): {e}")
        return
    now_str = datetime.now().isoformat()
    rep_data = {
            "session_id": session_id,
            "exercise": row.get("exercise", "unknown"),
            "symmetry": row.get("symmetry", 0.0),
            "range_of_motion": row.get("range_of_motion", 0.0),
            "posture": row.get("posture", 0.0),
            "control": row.get("control", 0.0),
            "rep_score": row.get("rep_score", 0.0),
            "rep_label": row.get("rep_label", "bad_rep"),
            "created_at": now_str
        }
        
    threading.Thread(target=_save_rep_background, args=(client, rep_data), daemon=True).start()


def get_history(exercise: str | None = None, limit: int = 50, user_id: str | None = None) -> list:
    """
    Retrieve session history, optionally filtered by exercise.
    RLS ensures users only see their own sessions.
    """
    client = _get_client()
    query = client.table("sessions").select("*").gt("total_reps", 0)
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


def get_user_by_email(email: str) -> dict | None:
    """
    Convenience wrapper: look up the current user's profile using their
    session user_id (already stored in st.session_state). The email
    parameter is accepted for backward-compatibility but the lookup is
    done by user_id via RLS so no cross-user data can be returned.
    """
    user_id = st.session_state.get("user_id")
    if not user_id:
        return None
    return get_user_profile(user_id)



def check_upload_limit(user_id: str, limit: int = 5) -> tuple[bool, str]:
    """
    Returns (is_allowed, error_message).
    is_allowed is True if the user has < `limit` uploads in the last hour.
    If a database error occurs, it returns (False, "error") to fail-safe.
    """
    import datetime
    client = _get_client()
    one_hour_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()
    try:
        res = client.table("upload_logs").select("id", count="exact").eq("user_id", user_id).gte("created_at", one_hour_ago).execute()
        count = res.count if res.count is not None else 0
        if count < limit:
            return True, ""
        return False, "limit_exceeded"
    except Exception as e:
        import logging
        logging.warning(f"Failed to check upload limit: {e}")
        # Fail safe (reject) on error, but tell caller it was an error
        return False, "db_error"

def log_upload(user_id: str) -> None:
    """
    Logs a video upload event for rate limiting.
    """
    client = _get_client()
    try:
        client.table("upload_logs").insert({"user_id": user_id}).execute()
    except Exception as e:
        import logging
        logging.warning(f"Failed to log upload: {e}")
