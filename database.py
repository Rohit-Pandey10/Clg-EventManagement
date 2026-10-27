"""
database.py
Database management module for College Event Management System (CEMS).
Handles SQLite schema creation, foreign key enforcement, and connection handling.
"""

import os
import sqlite3
from typing import Optional
from auth import hash_password

# Determine database path relative to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "college_events.db")


def get_connection() -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with row factory
    enabled and foreign key constraints strictly enforced.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Foreign key enforcement must be turned on per connection in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(default_admin_password: str = "admin123") -> None:
    """
    Initializes database tables if they do not exist.
    Also ensures at least one administrator account exists.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Table 1: users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'student')),
                full_name TEXT NOT NULL,
                roll_no TEXT UNIQUE,
                department TEXT,
                email TEXT UNIQUE
            );
        """)

        # Table 2: events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                event_date TEXT NOT NULL,
                venue TEXT NOT NULL,
                description TEXT,
                fee REAL NOT NULL DEFAULT 0,
                capacity INTEGER NOT NULL,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE SET NULL
            );
        """)

        # Table 3: registrations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrations (
                registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                registration_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('registered', 'cancelled')),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
                UNIQUE (user_id, event_id)
            );
        """)

        # Check if an admin exists
        cursor.execute("SELECT COUNT(*) AS admin_count FROM users WHERE role = 'admin';")
        admin_count = cursor.fetchone()["admin_count"]

        if admin_count == 0:
            # Dynamically hash the default admin password at initialization time
            # No plain-text password is saved into the database table
            admin_hash = hash_password(default_admin_password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, roll_no, department, email)
                VALUES (?, ?, 'admin', 'System Administrator', NULL, 'Administration', 'admin@college.edu');
            """, ("admin", admin_hash))
            print(f"[Database] Default admin account created: username='admin'")

        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"[Database Error] Initialization failed: {e}")
        raise
    finally:
        conn.close()


def has_any_admin() -> bool:
    """Helper to check if any admin exists in the database."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'admin';")
        row = cursor.fetchone()
        return row["count"] > 0
    finally:
        conn.close()


def create_admin_account(username: str, password: str, full_name: str, department: str = "Admin", email: Optional[str] = None) -> tuple[bool, str]:
    """
    Creates a new administrator account with salted PBKDF2 password hashing.
    """
    if not username.strip() or not password.strip() or not full_name.strip():
        return False, "Username, password, and full name are required."

    pw_hash = hash_password(password.strip())
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, roll_no, department, email)
            VALUES (?, ?, 'admin', ?, NULL, ?, ?);
        """, (username.strip(), pw_hash, full_name.strip(), department.strip(), email.strip() if email else None))
        conn.commit()
        return True, "Admin account created successfully!"
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "UNIQUE constraint failed: users.username" in str(e):
            return False, f"Username '{username}' is already taken."
        if "UNIQUE constraint failed: users.email" in str(e):
            return False, f"Email '{email}' is already registered."
        return False, f"Database constraint error: {str(e)}"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialization script executed successfully.")
