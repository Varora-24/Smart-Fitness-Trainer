# ================================================================
#  auth.py  –  Streamlit session-based authentication
# ================================================================
#  Provides require_login() guard for all pages, plus signup/login
#  forms backed by bcrypt password hashing and the SQLite users table.
# ================================================================

import bcrypt
import streamlit as st
import db


def _hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, stored_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except (ValueError, TypeError):
        # Invalid hash format (e.g. "!" for legacy account) → always reject
        return False


def _render_auth_forms() -> None:
    """Render login and signup tabs; set session_state on success."""
    st.markdown("### 🔐 Please log in or create an account to continue")

    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In")

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    user = db.get_user_by_email(email)
                    if user and _verify_password(password, user["password_hash"]):
                        st.session_state["user_id"] = user["id"]
                        st.session_state["email"] = user["email"]
                        st.session_state["display_name"] = user.get("display_name", "")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_name = st.text_input("Display Name (optional)", key="signup_name")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="signup_confirm"
            )
            submitted = st.form_submit_button("Create Account")

            if submitted:
                if not new_email or not new_password:
                    st.error("Email and password are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    existing = db.get_user_by_email(new_email)
                    if existing:
                        st.error("An account with this email already exists.")
                    else:
                        hashed = _hash_password(new_password)
                        user_id = db.create_user(
                            email=new_email,
                            password_hash=hashed,
                            display_name=new_name or None,
                        )
                        st.session_state["user_id"] = user_id
                        st.session_state["email"] = new_email
                        st.session_state["display_name"] = new_name or ""
                        st.success("Account created! Redirecting...")
                        st.rerun()


def require_login() -> None:
    """
    Call at the top of any Streamlit page that requires authentication.

    If the user is not logged in, renders a login/signup form and
    calls st.stop() to prevent the rest of the page from rendering.

    Session state keys set on successful auth:
      - user_id (int)
      - email (str)
      - display_name (str)
    """
    # Ensure DB schema is ready (idempotent)
    db.init_db()

    if "user_id" not in st.session_state:
        _render_auth_forms()
        st.stop()
