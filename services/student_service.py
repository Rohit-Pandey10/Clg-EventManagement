"""
services/student_service.py
Service handling all business logic, validation, and database operations for Student accounts.
Role enforcement: Only 'admin' users can create, update, or list student accounts.
"""

import sqlite3
import re
from typing import List, Dict, Any, Tuple, Optional
from database import get_connection
from auth import hash_password

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"


def validate_student_data(full_name: str, username: str, roll_no: str,
                          department: str, email: str, is_new: bool = True,
                          password: str = "") -> Tuple[bool, str]:
    """
    Validates form data for student account creation or update.
    """
    if not full_name.strip():
        return False, "Full Name cannot be empty."
    if not username.strip():
        return False, "Username cannot be empty."
    if len(username.strip()) < 3:
        return False, "Username must be at least 3 characters long."
    if not roll_no.strip():
        return False, "Roll Number cannot be empty."
    if is_new and not password.strip():
        return False, "Password cannot be empty for new students."
    if is_new and len(password.strip()) < 4:
        return False, "Password must be at least 4 characters long."

    clean_email = email.strip()
    if clean_email and not re.match(EMAIL_REGEX, clean_email):
        return False, "Please enter a valid email address (e.g. student@college.edu)."

    return True, ""


def create_student(full_name: str, username: str, password: str, roll_no: str,
                   department: str, email: str, admin_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Creates a new student account. Role check: Admin only.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return False, "Permission denied: Only administrators can create student accounts."

    is_valid, err_msg = validate_student_data(full_name, username, roll_no, department, email, is_new=True, password=password)
    if not is_valid:
        return False, err_msg

    pw_hash = hash_password(password.strip())
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, full_name, roll_no, department, email)
            VALUES (?, ?, 'student', ?, ?, ?, ?);
        """, (
            username.strip(),
            pw_hash,
            full_name.strip(),
            roll_no.strip().upper(),
            department.strip(),
            email.strip() if email.strip() else None
        ))
        conn.commit()
        return True, "Student account created successfully!"
    except sqlite3.IntegrityError as e:
        conn.rollback()
        err_str = str(e).lower()
        if "users.username" in err_str:
            return False, f"Username '{username.strip()}' is already taken."
        if "users.roll_no" in err_str:
            return False, f"Roll Number '{roll_no.strip().upper()}' is already registered."
        if "users.email" in err_str:
            return False, f"Email address '{email.strip()}' is already in use."
        return False, f"Integrity error: {str(e)}"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def update_student(user_id: int, full_name: str, roll_no: str, department: str,
                   email: str, password: Optional[str], admin_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Updates an existing student account.
    If password is provided, updates the password hash as well.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return False, "Permission denied: Only administrators can update student accounts."

    is_valid, err_msg = validate_student_data(full_name, "dummy", roll_no, department, email, is_new=False)
    if not is_valid:
        return False, err_msg

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # If a new password is provided, update it
        if password and password.strip():
            if len(password.strip()) < 4:
                return False, "Password must be at least 4 characters long."
            pw_hash = hash_password(password.strip())
            cursor.execute("""
                UPDATE users
                SET full_name = ?, roll_no = ?, department = ?, email = ?, password_hash = ?
                WHERE user_id = ? AND role = 'student';
            """, (
                full_name.strip(),
                roll_no.strip().upper(),
                department.strip(),
                email.strip() if email.strip() else None,
                pw_hash,
                user_id
            ))
        else:
            cursor.execute("""
                UPDATE users
                SET full_name = ?, roll_no = ?, department = ?, email = ?
                WHERE user_id = ? AND role = 'student';
            """, (
                full_name.strip(),
                roll_no.strip().upper(),
                department.strip(),
                email.strip() if email.strip() else None,
                user_id
            ))

        conn.commit()
        return True, "Student updated successfully!"
    except sqlite3.IntegrityError as e:
        conn.rollback()
        err_str = str(e).lower()
        if "users.roll_no" in err_str:
            return False, f"Roll Number '{roll_no.strip().upper()}' is already assigned to another student."
        if "users.email" in err_str:
            return False, f"Email address '{email.strip()}' is already in use."
        return False, f"Integrity error: {str(e)}"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_all_students(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all registered students (passwords omitted).
    Can filter by search_query across roll_no, full_name, username, department.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        base_query = """
            SELECT user_id, username, full_name, roll_no, department, email
            FROM users
            WHERE role = 'student'
        """
        params = []

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            base_query += """
                AND (roll_no LIKE ? OR full_name LIKE ? OR username LIKE ? OR department LIKE ? OR email LIKE ?)
            """
            params.extend([term, term, term, term, term])

        base_query += " ORDER BY roll_no ASC, full_name ASC;"
        cursor.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_student_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches details for a single student."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name, roll_no, department, email
            FROM users
            WHERE user_id = ? AND role = 'student';
        """, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
