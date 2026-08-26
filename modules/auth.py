"""
Authentication, Password Security & RBAC Module.
Handles bcrypt password hashing, credential verification, and user registration.
"""

import sqlite3
from typing import Any, Dict, Optional, Tuple
import bcrypt
from config.database import get_connection


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with a salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def register_user(
    username: str,
    password: str,
    full_name: str,
    role: str,
    phone: str = "",
    email: str = "",
    institution: str = "",
    department: str = "",
) -> Tuple[bool, str]:
    """
    Registers a new user into the database with enforced role validation.
    If the role is 'expert', an anonymized token and default profile are auto-created.
    """
    valid_roles = ("student", "college", "expert", "coordinator")
    if role not in valid_roles:
        return False, f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}"

    if not username or not password or not full_name:
        return False, "Username, password, and full name are required."

    conn = get_connection()
    cursor = conn.cursor()
    pwd_hash = hash_password(password)

    try:
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, full_name, role, phone, email, institution, department)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (username.strip(), pwd_hash, full_name.strip(), role, phone.strip(), email.strip(), institution.strip(), department.strip()),
        )
        user_id = cursor.lastrowid

        # Provision expert profile with anonymous token if role is expert
        if role == "expert":
            token = f"EXP-M{user_id:04d}"
            cursor.execute(
                """
                INSERT INTO expert_profiles (
                    user_id, token, industry_vertical, experience_years,
                    skills, hourly_rate_inr, bio
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    token,
                    "General Technology",
                    3,
                    "AI, Python, Software Engineering",
                    1500.0,
                    f"Verified industry consultant ({department or 'Tech'}).",
                ),
            )

        conn.commit()
        return True, "Registration successful."
    except sqlite3.IntegrityError:
        return False, "Username already exists. Please select another username."
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Validates user credentials against stored hash.
    Returns user dictionary if authenticated, None otherwise.
    """
    if not username or not password:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
    user = cursor.fetchone()
    conn.close()

    if user and verify_password(password, user["password_hash"]):
        user_dict = dict(user)
        # Exclude hash from the active session object for security
        user_dict.pop("password_hash", None)
        return user_dict
    return None
