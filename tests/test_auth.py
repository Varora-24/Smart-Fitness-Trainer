# ================================================================
#  tests/test_auth.py  –  Authentication unit tests
# ================================================================

import gc
import os
import sqlite3
import tempfile
import time
import pytest

# Patch DB_PATH before importing db/auth so tests use an isolated database
_TEST_DB_DIR = tempfile.mkdtemp()
_TEST_DB_PATH = os.path.join(_TEST_DB_DIR, "test_auth.db")

import db
db.DB_PATH = _TEST_DB_PATH

import auth


@pytest.fixture(autouse=True)
def fresh_db():
    """Reset the test database before each test."""
    # Remove the old DB file entirely to avoid locking issues on Windows
    for path in (_TEST_DB_PATH, _TEST_DB_PATH + ".pre_migration_backup"):
        if os.path.exists(path):
            try:
                os.unlink(path)
            except PermissionError:
                gc.collect()
                time.sleep(0.1)
                os.unlink(path)

    db.DB_PATH = _TEST_DB_PATH
    db.init_db()
    yield
    gc.collect()  # Force-close any lingering sqlite3 connections


def teardown_module():
    gc.collect()
    time.sleep(0.2)
    for path in (_TEST_DB_PATH, _TEST_DB_PATH + ".pre_migration_backup"):
        if os.path.exists(path):
            try:
                os.unlink(path)
            except PermissionError:
                pass  # Best-effort cleanup


class TestPasswordHashing:
    """Verify bcrypt hashing and verification logic."""

    def test_hash_is_not_plaintext(self):
        plaintext = "StrongP@ss123"
        hashed = auth._hash_password(plaintext)
        assert hashed != plaintext
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_correct_password_verifies(self):
        plaintext = "StrongP@ss123"
        hashed = auth._hash_password(plaintext)
        assert auth._verify_password(plaintext, hashed) is True

    def test_wrong_password_fails(self):
        hashed = auth._hash_password("CorrectPassword")
        assert auth._verify_password("WrongPassword", hashed) is False

    def test_invalid_hash_format_fails(self):
        """The legacy account uses '!' which is not valid bcrypt."""
        assert auth._verify_password("anything", "!") is False


class TestUserCreation:
    """Verify user CRUD in the database."""

    def test_signup_creates_user(self):
        hashed = auth._hash_password("TestPass123!")
        user_id = db.create_user("test@example.com", hashed, "Test User")
        assert user_id is not None
        assert user_id > 0

        user = db.get_user_by_email("test@example.com")
        assert user is not None
        assert user["email"] == "test@example.com"
        assert user["display_name"] == "Test User"
        # Password is stored as hash, not plaintext
        assert user["password_hash"] != "TestPass123!"
        assert user["password_hash"].startswith("$2")

    def test_duplicate_email_rejected(self):
        hashed = auth._hash_password("Pass1234!")
        db.create_user("dup@example.com", hashed, "First")
        with pytest.raises(sqlite3.IntegrityError):
            db.create_user("dup@example.com", hashed, "Second")

    def test_login_with_correct_credentials(self):
        plaintext = "MySecurePass1"
        hashed = auth._hash_password(plaintext)
        db.create_user("login@example.com", hashed, "Login User")

        user = db.get_user_by_email("login@example.com")
        assert user is not None
        assert auth._verify_password(plaintext, user["password_hash"]) is True

    def test_login_with_wrong_password(self):
        hashed = auth._hash_password("RightPassword")
        db.create_user("wrong@example.com", hashed, "User")

        user = db.get_user_by_email("wrong@example.com")
        assert user is not None
        assert auth._verify_password("WrongPassword", user["password_hash"]) is False

    def test_nonexistent_user_returns_none(self):
        assert db.get_user_by_email("nobody@example.com") is None

    def test_legacy_account_cannot_authenticate(self):
        """The migration-created legacy user has password_hash='!' and cannot log in."""
        user = db.get_user_by_email("legacy-owner@internal")
        if user is not None:
            assert auth._verify_password("legacy123", user["password_hash"]) is False
            assert auth._verify_password("", user["password_hash"]) is False
            assert auth._verify_password("anything", user["password_hash"]) is False


class TestUserProfile:
    """Verify profile update functionality."""

    def test_update_profile_fields(self):
        hashed = auth._hash_password("ProfilePass1")
        user_id = db.create_user("profile@example.com", hashed)

        db.update_user_profile(
            user_id,
            weight_kg=75.0,
            height_cm=180.0,
            age=30,
            sex="male",
            activity_level="moderate",
            fitness_goal="gain_muscle",
        )

        user = db.get_user_by_email("profile@example.com")
        assert user["weight_kg"] == 75.0
        assert user["height_cm"] == 180.0
        assert user["age"] == 30
        assert user["sex"] == "male"
        assert user["activity_level"] == "moderate"
        assert user["fitness_goal"] == "gain_muscle"

    def test_update_ignores_disallowed_fields(self):
        """Fields not in the allowed set should be silently ignored."""
        hashed = auth._hash_password("SafePass1")
        user_id = db.create_user("safe@example.com", hashed)

        # password_hash is NOT in the allowed update set
        db.update_user_profile(user_id, password_hash="hacked!")

        user = db.get_user_by_email("safe@example.com")
        assert user["password_hash"] == hashed  # unchanged
