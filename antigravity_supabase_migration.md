# Antigravity Task Prompt — Migrate to Supabase (Postgres + Auth)

Copy everything below into Antigravity as a single task. This touches secrets management, a real schema migration, and an external network dependency — read the whole thing before starting, and do not skip the safety steps around existing data.

---

## Context

Repo: `https://github.com/Varora-24/Smart-Fitness-Trainer`

Current state: `db.py` uses raw `sqlite3` against a local `workout_history.db` file. `auth.py` hand-rolls signup/login with `bcrypt`. This task replaces both: the database moves to a dedicated Supabase Postgres project, and authentication moves to Supabase Auth, eliminating the custom bcrypt code entirely.

**A new, dedicated Supabase project has already been created for this repo** (not shared with any other project). The user will provide:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- A pooler connection string (port 6543)

**None of these are ever hardcoded or committed.** See Part 1.

---

## Part 1 — Secrets management (do this before writing any migration code)

### 1.1 Local development: `.env` + `python-dotenv`

Add `python-dotenv>=1.0.0` to `requirements.txt`. Create `.env.example` (committed, no real values) documenting required variables:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```
Add `.env` (the real file, with actual values) to `.gitignore` — confirm it's not already accidentally tracked with `git status` before proceeding.

### 1.2 Streamlit deployment: `.streamlit/secrets.toml`

Streamlit Cloud has a native secrets manager. Create `.streamlit/secrets.toml.example` (committed, placeholder values) and add the real `.streamlit/secrets.toml` to `.gitignore`. Code should read from `st.secrets` when running under Streamlit, falling back to `os.environ` (populated via `.env`/`python-dotenv`) for any non-Streamlit context (e.g. `train_model.py`, standalone scripts):
```python
import os
import streamlit as st

def get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ[key]
```

### 1.3 Add `supabase-py` and `psycopg2-binary`

```
supabase>=2.3.0
psycopg2-binary>=2.9.9
```
Exact-pin both once a working version is confirmed, consistent with how every other dependency in this repo is now pinned.

---

## Part 2 — Schema migration (SQLite → Postgres)

### 2.1 Translate the existing schema

Current SQLite tables: `users`, `sessions` (with `user_id`), `reps` (with `session_id`). Translate to Postgres, using Supabase's native `auth.users` table for identity instead of a custom `users` table (see Part 3) — the app-specific `users` table becomes a `profiles` table that extends Supabase Auth's built-in user, following Supabase's standard pattern:

```sql
-- profiles table, one row per Supabase Auth user, linked by id
create table public.profiles (
    id uuid references auth.users(id) primary key,
    display_name text,
    weight_kg real,
    height_cm real,
    age integer,
    sex text,
    activity_level text,
    fitness_goal text,
    created_at timestamptz default now()
);

create table public.sessions (
    id bigint generated always as identity primary key,
    user_id uuid references auth.users(id) not null,
    exercise text not null,
    started_at timestamptz not null,
    ended_at timestamptz,
    total_reps integer,
    clean_reps integer,
    bad_reps integer,
    calories real,
    avg_rep_score real
);

create table public.reps (
    id bigint generated always as identity primary key,
    session_id bigint references public.sessions(id) not null,
    exercise text not null,
    symmetry real,
    range_of_motion real,
    posture real,
    control real,
    rep_score real,
    rep_label text,
    created_at timestamptz default now()
);
```
Adjust column names/types to exactly match whatever `db.py` currently actually defines — read the current schema in full before finalizing this, do not assume the sketch above is complete or exactly correct.

### 2.2 Enable Row Level Security (RLS) — do not skip this

This is the single most important Postgres-specific step and has no SQLite equivalent. Without RLS, any authenticated user could query any other user's data through Supabase's API. Enable it and add policies restricting each table to its owning user:

```sql
alter table public.profiles enable row level security;
alter table public.sessions enable row level security;
alter table public.reps enable row level security;

create policy "Users can view own profile" on public.profiles
    for select using (auth.uid() = id);
create policy "Users can update own profile" on public.profiles
    for update using (auth.uid() = id);

create policy "Users can view own sessions" on public.sessions
    for select using (auth.uid() = user_id);
create policy "Users can insert own sessions" on public.sessions
    for insert with check (auth.uid() = user_id);

create policy "Users can view own reps" on public.reps
    for select using (
        session_id in (select id from public.sessions where user_id = auth.uid())
    );
create policy "Users can insert own reps" on public.reps
    for insert with check (
        session_id in (select id from public.sessions where user_id = auth.uid())
    );
```
Run these via the Supabase SQL Editor (or a migration file under `supabase/migrations/`, if using the Supabase CLI — prefer this if it's available, since it makes the schema versioned and reviewable in the repo rather than only existing in the dashboard).

### 2.3 Migrate the existing data — preserve it, do not silently drop it

The same principle applies here as the earlier SQLite `users` table migration: back up first, and do not destroy anything irreversibly.

1. Before touching anything, confirm `workout_history.db` and its `.pre_migration_backup` sibling from the earlier migration both still exist and are untouched.
2. Write a one-off `scratch/migrate_to_supabase.py` script that:
   - Reads all rows from local `sessions` and `reps` tables (skip the legacy `users` row and anything tied to it — that data was already established as intentionally inaccessible, see the earlier decision; do not create a Supabase Auth user for it).
   - For any *real* (non-legacy) session/rep data, insert it into the new Supabase tables via the service role key (bypasses RLS for a one-time admin migration).
   - Prints a summary of exactly how many rows were migrated.
3. Delete this script from `scratch/` after running it once, same as the earlier one-off label-fix script.

---

## Part 3 — Replace `auth.py` with Supabase Auth

### 3.1 Rewrite `auth.py`

```python
from supabase import create_client, Client
import streamlit as st

def get_supabase_client() -> Client:
    return create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_ANON_KEY"))

def require_login():
    if "supabase_session" not in st.session_state:
        # render sign up / log in forms using supabase.auth.sign_up() /
        # supabase.auth.sign_in_with_password(), store the returned session
        # (including access token) in st.session_state
        ...
        st.stop()
```
Use `supabase.auth.sign_up(email, password)` and `supabase.auth.sign_in_with_password(email, password)` — Supabase handles password hashing, email verification (optional, can be disabled for now in Project Settings → Auth if you don't want to set up email sending yet), and session/token management. Delete the `bcrypt` dependency and all custom password-hashing code entirely — do not keep it around "just in case."

### 3.2 Session persistence across Streamlit page reruns

Confirm the same cross-page persistence behavior that was explicitly tested in the original `auth.py` migration still holds here — store the Supabase session/access token in `st.session_state`, and re-verify it's still valid (not expired) at the top of `require_login()` on every page, refreshing if needed via `supabase.auth.refresh_session()`.

### 3.3 Every downstream query must use the authenticated user's own token, not the anon key alone

Once logged in, all data reads/writes for that user should happen through a Supabase client configured with their session (so RLS policies correctly scope every query to `auth.uid()`), not through a client using only the anon key. Confirm this pattern is used consistently in `db.py`, `pages/2_📊_History.py`, `pages/4_🥗_Nutrition.py`, and anywhere else `require_login()` gates access.

---

## Part 4 — Rewrite `db.py` against Supabase

Replace every `sqlite3` call with the equivalent `supabase-py` client call (preferred, gets RLS enforcement automatically) or, where raw SQL is genuinely needed, `psycopg2` against the pooler connection string from Part 1. Prefer the `supabase-py` client for anything user-scoped; reserve direct `psycopg2` only for admin/migration-style operations that intentionally need to bypass RLS (like Part 2.3's one-off script).

```python
# example: saving a completed rep
def save_rep(session_id: int, exercise: str, symmetry: float, ...):
    client = get_authenticated_client()  # uses the logged-in user's session
    client.table("reps").insert({
        "session_id": session_id,
        "exercise": exercise,
        "symmetry": symmetry,
        ...
    }).execute()
```

Add explicit, user-visible error handling for network failures — this app now depends on an external service that can be temporarily unreachable, unlike a local SQLite file:
```python
try:
    client.table("sessions").select("*").execute()
except Exception as e:
    st.error("Could not reach the database right now. Your workout data may not have been saved. Please check your connection and try again.")
    logger.error(f"Supabase query failed: {e}")
```
Every page that reads/writes data should degrade gracefully with a clear message, not crash with a raw traceback, if Supabase is temporarily unreachable.

---

## Part 5 — Update the test suite

Existing tests (`test_session_tracker.py`, `test_auth.py`, etc.) currently exercise real SQLite via `tmp_path`. Do not attempt to spin up a real Postgres/Supabase connection in CI — that's a heavier, separate decision (Supabase CLI + local Docker Postgres) worth flagging as a Roadmap item, not doing now. Instead:
- Mock the `supabase-py` client (`unittest.mock.MagicMock` standing in for `Client`) in all unit tests, asserting the correct `.table(...).insert(...)`/`.select(...)` calls were made with the correct arguments, the same way `pyttsx3` is already mocked in `test_voice_coach.py`.
- Rewrite `test_auth.py` to mock `supabase.auth.sign_up`/`sign_in_with_password` rather than testing bcrypt hashing directly (that logic no longer exists in this codebase).

**Verification**: `pytest -v` must stay fully green with the new mocked approach — no test should require network access or a real Supabase project to pass in CI.

---

## Part 6 — Documentation

Update `README.md`:
- Add a "Setup" subsection under installation instructions: create a Supabase project, run the SQL from Part 2.1/2.2 via the SQL Editor (or `supabase/migrations/` if using the CLI), copy `.env.example` → `.env` and fill in real values.
- Update the architecture description to reflect Postgres/Supabase instead of SQLite.
- Add a note to Known Limitations: the app now requires network connectivity to Supabase for all account/history/nutrition features — the live trainer's core pose-detection loop itself does not depend on it and continues working offline once a session is authenticated, but data won't save without connectivity.

---

## Verification checklist

1. `ruff check .`, `mypy . --ignore-missing-imports`, `bandit -r .` — all clean. Bandit should show **zero** SQL-injection-pattern findings in the new Supabase-client code (parameterized by the client library itself) — flag anywhere raw SQL string interpolation was used instead of the client's query builder.
2. `pip-audit --local --ignore-vuln PYSEC-2026-1805` — zero *new* vulnerabilities from `supabase`/`psycopg2-binary`.
3. `pytest -v` — all tests green using mocked Supabase clients, no real network calls in the test suite.
4. Confirm `.env`, `.streamlit/secrets.toml` (the real ones, not the `.example` files) are in `.gitignore` and `git status` shows them as untracked, never staged.
5. Manually run `streamlit run Home.py` with real `.env`/`secrets.toml` values filled in: sign up a brand-new test account, confirm it appears in Supabase's Auth dashboard, complete a profile, run through nutrition/supplements/history, confirm a live-trainer session actually writes a row to Supabase's `sessions`/`reps` tables (check via the Supabase Table Editor directly, not just trusting the app's own success message).
6. **Test RLS is actually enforced**, not just present in the SQL: sign up two separate test accounts, log workout data under account A, log in as account B, and confirm account B's History page shows zero of account A's data. This is the single most important security check in this entire task — do not skip it.
7. Push commits (one per part, 6 minimum), confirm via the GitHub API that CI reaches `success` on the new commit — note that CI's test suite uses mocked clients per Part 5, so CI passing does not itself prove Part 6.5/6.6's real-Supabase manual checks were done; both are required.

---

## Constraints

- Do not commit any real Supabase URL, key, or connection string anywhere in the repo, including in commit messages, code comments, or test fixtures.
- Do not delete `workout_history.db` or its backup — leave the SQLite files in place, untouched, as a historical artifact/fallback, even after the migration is complete and verified.
- Do not skip Part 2.2's RLS policies under any circumstance, even temporarily "to test faster" — an app with real user accounts and no RLS means every user can read every other user's data through the API.
- If Part 2.3's data migration reveals any ambiguity about what should or shouldn't be migrated, stop and ask rather than guessing, the same discipline used for the earlier legacy-account decision.
