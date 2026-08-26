"""
Tests for modules/auth.py.
Validates bcrypt password hashing, verification, registration constraints,
anonymized expert token provisioning, and authentication flows.
"""

import pytest
import sqlite3
from config.database import init_db, get_connection
from modules.auth import (
    hash_password,
    verify_password,
    register_user,
    authenticate_user,
)


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Provisions a clean in-memory SQLite database for every test."""
    test_db = ":memory:"
    init_db(test_db)
    
    # Patch get_connection to return this shared in-memory connection
    conn = sqlite3.connect(test_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Initialize full schema in memory
    init_db(test_db)
    monkeypatch.setattr("modules.auth.get_connection", lambda: conn)
    monkeypatch.setattr("config.database.get_connection", lambda: conn)
    yield conn
    conn.close()


def test_password_hashing():
    raw_pwd = "SecurePassword@2026"
    hashed = hash_password(raw_pwd)
    
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_register_student_success():
    ok, msg = register_user(
        username="student_test_1",
        password="password123",
        full_name="Aarav Test",
        role="student",
        phone="+919999988888",
        email="aarav@test.edu",
        institution="RVCE",
        department="CSE"
    )
    assert ok is True
    assert "successful" in msg.lower()


def test_register_duplicate_username_fails():
    register_user("unique_user", "pass123", "User One", "student")
    ok, msg = register_user("unique_user", "pass456", "User Two", "student")
    
    assert ok is False
    assert "already exists" in msg.lower()


def test_register_invalid_role_fails():
    ok, msg = register_user("bad_role_user", "pass123", "Invalid Role", "superadmin")
    assert ok is False
    assert "invalid role" in msg.lower()


def test_expert_registration_auto_generates_token(setup_test_db):
    conn = setup_test_db
    ok, msg = register_user(
        username="expert_ai_test",
        password="password123",
        full_name="Dr. Expert",
        role="expert",
        phone="+919876543210",
        email="expert@ai.org",
        institution="AI Lab",
        department="GenAI"
    )
    assert ok is True
    
    # Verify anonymous expert profile was automatically created
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expert_profiles WHERE bio LIKE '%Verified industry consultant%'")
    profile = cursor.fetchone()
    
    assert profile is not None
    assert profile["token"].startswith("EXP-M")
    assert profile["rating"] == 5.0


def test_authenticate_user_success_and_failure():
    register_user("auth_user", "correct_pwd", "Auth User", "coordinator")
    
    # Valid login
    user = authenticate_user("auth_user", "correct_pwd")
    assert user is not None
    assert user["username"] == "auth_user"
    assert user["role"] == "coordinator"
    assert "password_hash" not in user  # Ensure hash is stripped for security
    
    # Invalid login - wrong password
    assert authenticate_user("auth_user", "wrong_pwd") is None
    
    # Invalid login - non-existent user
    assert authenticate_user("ghost_user", "pass") is None
