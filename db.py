# ================================================================
#  db.py  –  SQLite database layer for workout history
# ================================================================

import logging
import os
import shutil
import sqlite3
from datetime import datetime

logger = logging.getLogger("db")

DB_PATH = "workout_history.db"
_BACKUP_PATH = "workout_history.db.pre_migration_backup"


def get_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _needs_migration(conn: sqlite3.Connection) -> bool:
    """Check if the sessions table is missing the user_id column."""
    cursor = conn.execute("PRAGMA table_info(sessions);")
    columns = [row[1] for row in cursor.fetchall()]
    return "user_id" not in columns


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _run_migration(conn: sqlite3.Connection) -> None:
    """
    One-time migration: add users table and user_id FK to sessions.

    Existing rows are assigned to a legacy user account that has an
    invalid bcrypt hash ("!") making it permanently unauthenticatable.
    Reps inherit ownership through their session_id FK — no user_id
    column is added to the reps table.
    """
    # Step 0: backup before any schema changes
    if os.path.isfile(DB_PATH):
        shutil.copy2(DB_PATH, _BACKUP_PATH)
        logger.info("Pre-migration backup created: %s", _BACKUP_PATH)

    cursor = conn.cursor()

    # Step 1: create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TEXT NOT NULL,
            weight_kg REAL,
            height_cm REAL,
            age INTEGER,
            sex TEXT,
            activity_level TEXT,
            fitness_goal TEXT
        );
    """)

    # Step 2: insert legacy user (un-loginable — "!" is not valid bcrypt)
    cursor.execute(
        "SELECT id FROM users WHERE email = ?;",
        ("legacy-owner@internal",),
    )
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            """INSERT INTO users (email, password_hash, display_name, created_at)
               VALUES (?, ?, ?, ?);""",
            (
                "legacy-owner@internal",
                "!",                       # not valid bcrypt → can never authenticate
                "Legacy Data",
                datetime.now().isoformat(),
            ),
        )
        legacy_id = cursor.lastrowid
        logger.info("Legacy user created with id=%d", legacy_id)
    else:
        legacy_id = row[0]

    # Step 3: add user_id column to sessions if missing
    if _table_exists(conn, "sessions"):
        col_cursor = conn.execute("PRAGMA table_info(sessions);")
        columns = [r[1] for r in col_cursor.fetchall()]
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id);")
            cursor.execute("UPDATE sessions SET user_id = ?;", (legacy_id,))
            logger.info("Migrated sessions table: user_id backfilled with legacy user %d", legacy_id)

    conn.commit()


def init_db() -> None:
    """Initialize the SQLite database schema if tables do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Users table (created first so FKs resolve)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            created_at TEXT NOT NULL,
            weight_kg REAL,
            height_cm REAL,
            age INTEGER,
            sex TEXT,
            activity_level TEXT,
            fitness_goal TEXT
        );
    """)

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
            avg_rep_score REAL NOT NULL,
            user_id INTEGER REFERENCES users(id)
        );
    """)

    # Reps table (ownership via session_id → sessions.user_id JOIN)
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

    # Run migration if existing DB is missing user_id on sessions
    if _needs_migration(conn):
        _run_migration(conn)

    conn.close()


# ── User functions ──────────────────────────────────────────────

def create_user(email: str, password_hash: str, display_name: str | None = None) -> int:
    """
    Insert a new user and return their id.

    Parameters
    ----------
    email : str — must be unique
    password_hash : str — bcrypt hash, never plaintext
    display_name : str | None

    Returns
    -------
    user_id : int
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO users (email, password_hash, display_name, created_at)
           VALUES (?, ?, ?, ?);""",
        (email, password_hash, display_name, datetime.now().isoformat()),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str) -> dict | None:
    """
    Look up a user by email.

    Returns
    -------
    dict with user fields, or None if not found.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?;", (email,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def update_user_profile(user_id: int, **fields: object) -> None:
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

    set_clause = ", ".join(f"{col} = ?" for col in to_update)
    values = list(to_update.values()) + [user_id]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE users SET {set_clause} WHERE id = ?;",  # nosec B608
        values,
    )
    conn.commit()
    conn.close()


# ── Session / rep functions ──────────────────────────────────────

def save_session(summary_dict: dict, exercise: str, user_id: int | None = None) -> int:
    """
    Save a workout session summary to the sessions table.

    Parameters
    ----------
    summary_dict : dict containing clean_reps, bad_reps, calories, etc.
    exercise : str name of the exercise practiced
    user_id : optional user who owns the session

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
            calories, duration_secs, avg_rep_score, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        now_str,
        exercise,
        summary_dict.get("total_reps", 0),
        summary_dict.get("clean_reps", 0),
        summary_dict.get("bad_reps", 0),
        summary_dict.get("calories", 0.0),
        summary_dict.get("duration_secs", 0.0),
        summary_dict.get("avg_rep_score", 0.0),
        user_id,
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


def get_history(exercise: str | None = None, limit: int = 50,
                user_id: int | None = None) -> list:
    """
    Retrieve session history, optionally filtered by exercise and/or user.

    Returns
    -------
    list of Row objects
    """
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None and exercise:
        cursor.execute("""
            SELECT * FROM sessions
            WHERE user_id = ? AND exercise = ?
            ORDER BY date DESC
            LIMIT ?;
        """, (user_id, exercise, limit))
    elif user_id is not None:
        cursor.execute("""
            SELECT * FROM sessions
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?;
        """, (user_id, limit))
    elif exercise:
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


def get_reps_for_user(user_id: int, limit: int = 200) -> list:
    """
    Retrieve rep history for a user via JOIN through sessions.user_id.

    Returns
    -------
    list of dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.* FROM reps r
        JOIN sessions s ON r.session_id = s.id
        WHERE s.user_id = ?
        ORDER BY r.timestamp DESC
        LIMIT ?;
    """, (user_id, limit))
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
    # rep_ids are internal generated integers, placeholders is built from len(rep_ids).
    query = f"UPDATE reps SET session_id = ? WHERE id IN ({placeholders});"  # nosec B608
    cursor.execute(query, [session_id] + rep_ids)
    conn.commit()
    conn.close()
