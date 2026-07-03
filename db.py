# ================================================================
#  db.py  –  SQLite database layer for workout history
# ================================================================

import sqlite3
from datetime import datetime

DB_PATH = "workout_history.db"

def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize the SQLite database schema if tables do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            exercise TEXT NOT NULL,
            total_reps INTEGER NOT NULL,
            clean_reps INTEGER NOT NULL,
            bad_reps INTEGER NOT NULL,
            calories REAL NOT NULL,
            duration_secs REAL NOT NULL,
            avg_rep_score REAL NOT NULL
        );
    """)

    # Reps table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            exercise TEXT NOT NULL,
            symmetry REAL NOT NULL,
            range_of_motion REAL NOT NULL,
            posture REAL NOT NULL,
            control REAL NOT NULL,
            rep_score REAL NOT NULL,
            rep_label TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()

def save_session(summary_dict: dict, exercise: str) -> int:
    """
    Save a workout session summary to the sessions table.
    
    Parameters
    ----------
    summary_dict : dict containing clean_reps, bad_reps, calories, etc.
    exercise : str name of the exercise practiced
    
    Returns
    -------
    session_id : int of the inserted session
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_str = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO sessions (
            date, exercise, total_reps, clean_reps, bad_reps, 
            calories, duration_secs, avg_rep_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        now_str,
        exercise,
        summary_dict.get("total_reps", 0),
        summary_dict.get("clean_reps", 0),
        summary_dict.get("bad_reps", 0),
        summary_dict.get("calories", 0.0),
        summary_dict.get("duration_secs", 0.0),
        summary_dict.get("avg_rep_score", 0.0)
    ))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def save_rep(row: dict, session_id: int | None = None) -> int:
    """
    Save a completed rep's metrics to the reps table.
    
    Parameters
    ----------
    row : dict of feature metrics for the rep
    session_id : optional foreign key ID linking to a session
    
    Returns
    -------
    rep_id : int of the inserted rep
    """
    conn = get_connection()
    cursor = conn.cursor()

    now_str = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO reps (
            session_id, exercise, symmetry, range_of_motion, 
            posture, control, rep_score, rep_label, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        session_id,
        row.get("exercise", "unknown"),
        row.get("symmetry", 0.0),
        row.get("range_of_motion", 0.0),
        row.get("posture", 0.0),
        row.get("control", 0.0),
        row.get("rep_score", 0.0),
        row.get("rep_label", "bad_rep"),
        now_str
    ))
    rep_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rep_id

def get_history(exercise: str | None = None, limit: int = 50) -> list:
    """
    Retrieve session history, optionally filtered by exercise.
    
    Returns
    -------
    list of Row objects
    """
    conn = get_connection()
    cursor = conn.cursor()

    if exercise:
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE exercise = ? 
            ORDER BY date DESC 
            LIMIT ?;
        """, (exercise, limit))
    else:
        cursor.execute("""
            SELECT * FROM sessions 
            ORDER BY date DESC 
            LIMIT ?;
        """, (limit,))
    
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def link_reps_to_session(session_id: int, rep_ids: list) -> None:
    """Link a list of rep IDs to a session ID."""
    if not rep_ids:
        return
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(rep_ids))
    cursor.execute(f"""
        UPDATE reps SET session_id = ? 
        WHERE id IN ({placeholders});
    """, [session_id] + rep_ids)
    conn.commit()
    conn.close()
