"""
auth.py
Authentication module for the College Event Management System.
Handles secure password hashing using PBKDF2-HMAC-SHA256, verification,
and user authentication logic.
"""

import hashlib
import secrets
import sqlite3
from typing import Optional, Tuple, Dict, Any


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using PBKDF2-HMAC-SHA256 with a random salt.
    Format returned: salt$hash
    """
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    ).hex()
    return f"{salt}${key}"


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """
    Verifies a plain-text password against a stored 'salt$hash' string.
    Uses secrets.compare_digest to prevent timing attacks.
    """
    try:
        salt, expected_key = stored_hash.split("$", 1)
        calculated_key = hashlib.pbkdf2_hmac(
            "sha256",
            provided_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        ).hex()
        return secrets.compare_digest(expected_key, calculated_key)
    except Exception:
        return False


def authenticate_user(username: str, password: str, get_db_connection_func) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Verifies user credentials against the database.
    Returns (user_dict, message). If authentication fails, user_dict is None.
    """
    clean_username = username.strip()
    clean_password = password.strip()

    if not clean_username or not clean_password:
        return None, "Please enter both username and password."

    conn = get_db_connection_func()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT user_id, username, password_hash, role, full_name, roll_no, department, email
            FROM users
            WHERE username = ?
            """,
            (clean_username,)
        )
        row = cursor.fetchone()

        if not row:
            return None, "Invalid username or password."

        stored_hash = row["password_hash"]
        if not verify_password(stored_hash, clean_password):
            return None, "Invalid username or password."

        # Return session-safe dictionary (excluding password hash)
        user_info = {
            "user_id": row["user_id"],
            "username": row["username"],
            "role": row["role"],
            "full_name": row["full_name"],
            "roll_no": row["roll_no"],
            "department": row["department"],
            "email": row["email"]
        }
        return user_info, "Login successful!"

    except sqlite3.Error as e:
        return None, f"Database error during authentication: {str(e)}"
    finally:
        conn.close()
