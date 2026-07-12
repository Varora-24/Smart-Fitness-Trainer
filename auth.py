# ================================================================
#  auth.py  –  Streamlit session-based authentication
# ================================================================

import os
import streamlit as st
from supabase import create_client, Client

def get_secret(key: str) -> str:
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ[key]

def get_supabase_client() -> Client:
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_ANON_KEY")
    return create_client(url, key)

def get_authenticated_client() -> Client:
    """Return a Supabase client initialized with the current user's session."""
    client = get_supabase_client()
    if "supabase_session" in st.session_state:
        session = st.session_state["supabase_session"]
        client.auth.set_session(session.access_token, session.refresh_token)
    return client

def _render_auth_forms() -> None:
    st.markdown("### 🔐 Please log in or create an account to continue")
    tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

    client = get_supabase_client()

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In")
            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    try:
                        response = client.auth.sign_in_with_password({"email": email, "password": password})
                        if response.session and response.user:
                            st.session_state["supabase_session"] = response.session
                            st.session_state["user_id"] = response.user.id
                            st.session_state["email"] = response.user.email
                            st.rerun()
                    except Exception as e:
                        st.error(f"Invalid email or password. Details: {e}")

    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account")
            if submitted:
                if not new_email or not new_password:
                    st.error("Email and password are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    try:
                        response = client.auth.sign_up({"email": new_email, "password": new_password})
                        if response.session and response.user:
                            st.session_state["supabase_session"] = response.session
                            st.session_state["user_id"] = response.user.id
                            st.session_state["email"] = response.user.email
                            st.success("Account created! Redirecting...")
                            st.rerun()
                        else:
                            st.info("Account created! Please verify your email to log in.")
                    except Exception as e:
                        st.error(f"Error creating account: {e}")

def require_login() -> None:
    """
    Call at the top of any Streamlit page that requires authentication.
    """
    if "supabase_session" not in st.session_state:
        _render_auth_forms()
        st.stop()
        return
    
    client = get_supabase_client()
    session = st.session_state["supabase_session"]
    try:
        # Refresh session if needed
        res = client.auth.set_session(session.access_token, session.refresh_token)
        if res.session:
            st.session_state["supabase_session"] = res.session
    except Exception:
        # Session expired or invalid
        st.session_state.pop("supabase_session", None)
        st.session_state.pop("user_id", None)
        st.session_state.pop("email", None)
        st.rerun()

def logout() -> None:
    client = get_authenticated_client()
    client.auth.sign_out()
    st.session_state.pop("supabase_session", None)
    st.session_state.pop("user_id", None)
    st.session_state.pop("email", None)
    st.session_state.pop("display_name", None)
    st.rerun()
