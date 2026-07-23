# ================================================================
#  tests/test_auth.py  –  Authentication unit tests (Supabase Mock)
# ================================================================

import pytest
import streamlit as st
from unittest.mock import MagicMock, patch

import core.utils.auth as auth
import core.data.db as db

@pytest.fixture(autouse=True)
def mock_streamlit_session():
    """Mock Streamlit session state with a dict before each test."""
    fake_state: dict = {}
    with patch("streamlit.session_state", fake_state):
        yield fake_state

@pytest.fixture
def mock_supabase():
    """Mock the Supabase client."""
    with patch("core.utils.auth.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        # Also mock get_secret to return dummy values to avoid KeyError
        with patch("core.utils.auth.get_secret", side_effect=lambda key: f"dummy_{key}"):
            yield mock_client

class TestAuthFunctions:
    """Verify Supabase auth wrappers."""

    def test_require_login_redirects_if_not_logged_in(self, mock_supabase):
        # When no session exists, require_login calls _render_auth_forms and stops
        with patch("core.utils.auth._render_auth_forms") as mock_render:
            with patch("streamlit.stop") as mock_stop:
                auth.require_login()
                mock_render.assert_called_once()
                mock_stop.assert_called_once()

    def test_require_login_refreshes_session(self, mock_supabase):
        # When session exists, require_login attempts to refresh it
        st.session_state["supabase_session"] = MagicMock(access_token="tok1", refresh_token="ref1")
        
        mock_res = MagicMock()
        mock_res.session = MagicMock(access_token="tok2")
        mock_supabase.auth.set_session.return_value = mock_res
        
        # Prevent st.stop from raising if called
        with patch("streamlit.stop"):
            auth.require_login()
            
        mock_supabase.auth.set_session.assert_called_with("tok1", "ref1")
        assert st.session_state["supabase_session"].access_token == "tok2"

    def test_require_login_clears_on_error(self, mock_supabase):
        st.session_state["supabase_session"] = MagicMock(access_token="tok1", refresh_token="ref1")
        st.session_state["user_id"] = "user1"
        st.session_state["email"] = "test@test.com"
        
        # Simulate invalid session
        mock_supabase.auth.set_session.side_effect = Exception("Expired")
        
        with patch("streamlit.rerun") as mock_rerun:
            auth.require_login()
            
        assert "supabase_session" not in st.session_state
        assert "user_id" not in st.session_state
        mock_rerun.assert_called_once()

    def test_logout(self, mock_supabase):
        st.session_state["supabase_session"] = MagicMock()
        st.session_state["user_id"] = "user1"
        
        with patch("streamlit.rerun") as mock_rerun:
            auth.logout()
            
        mock_supabase.auth.sign_out.assert_called_once()
        assert "supabase_session" not in st.session_state
        assert "user_id" not in st.session_state
        mock_rerun.assert_called_once()


class TestUserProfile:
    """Verify profile functions use Supabase."""

    @patch("core.data.db._get_client")
    def test_get_user_profile(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Setup mock return data
        mock_res = MagicMock()
        mock_res.data = [{"id": "user1", "display_name": "Test User"}]
        mock_client.table().select().eq().execute.return_value = mock_res
        
        profile = db.get_user_profile("user1")
        assert profile is not None
        assert profile["display_name"] == "Test User"
        mock_client.table.assert_called_with("profiles")

    @patch("core.data.db._get_client")
    def test_update_profile_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        db.update_user_profile(
            "user1",
            weight_kg=75.0,
            height_cm=180.0,
            invalid_field="hacked"
        )
        
        # Ensure invalid_field is not in the upsert data
        args, _ = mock_client.table().upsert.call_args
        data = args[0]
        assert "invalid_field" not in data
        assert data["weight_kg"] == 75.0
        assert data["id"] == "user1"
