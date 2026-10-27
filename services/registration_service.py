"""
services/registration_service.py
Service handling all business logic, validation, capacity checks, and database
operations for event registrations.
Role enforcement:
- Students can register and cancel their own registrations.
- Admins can view all registrations and filter by event/student.
"""

from datetime import datetime, date
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
from database import get_connection


def register_for_event(user_id: int, event_id: int, current_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Registers a student for an event.
    Enforces:
    - User must be a student and can only register for themselves.
    - Event must exist and must not be in the past.
    - Capacity check and registration are executed atomically within a SQLite transaction.
    - If student previously cancelled, reactivates the registration.
    """
    if not current_user:
        return False, "You must be logged in to register."

    # Enforce role and self-registration
    if current_user.get("role") != "student":
        return False, "Only students can register for events."
    if current_user.get("user_id") != user_id:
        return False, "Permission denied: You cannot register on behalf of another student."

    conn = get_connection()
    try:
        # Using context manager for transaction management (BEGIN ... COMMIT/ROLLBACK)
        with conn:
            cursor = conn.cursor()

            # 1. Fetch event details
            cursor.execute("""
                SELECT title, event_date, capacity
                FROM events
                WHERE event_id = ?;
            """, (event_id,))
            event = cursor.fetchone()

            if not event:
                return False, "The selected event could not be found."

            # 2. Check if event is in the past
            today_str = date.today().isoformat()
            if event["event_date"] < today_str:
                return False, f"Registration closed: '{event['title']}' is already in the past."

            # 3. Check existing registration
            cursor.execute("""
                SELECT registration_id, status
                FROM registrations
                WHERE user_id = ? AND event_id = ?;
            """, (user_id, event_id))
            existing_reg = cursor.fetchone()

            if existing_reg and existing_reg["status"] == "registered":
                return False, "You are already registered for this event."

            # 4. Check available capacity (count active registrations)
            cursor.execute("""
                SELECT COUNT(*) AS active_count
                FROM registrations
                WHERE event_id = ? AND status = 'registered';
            """, (event_id,))
            active_count = cursor.fetchone()["active_count"]

            if active_count >= event["capacity"]:
                return False, f"Event is full! Capacity limit ({event['capacity']} seats) reached."

            # 5. Insert or Reactivate
            reg_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if existing_reg:
                cursor.execute("""
                    UPDATE registrations
                    SET status = 'registered', registration_date = ?
                    WHERE registration_id = ?;
                """, (reg_date_str, existing_reg["registration_id"]))
                return True, f"Registration reactivated successfully for '{event['title']}'!"
            else:
                cursor.execute("""
                    INSERT INTO registrations (user_id, event_id, registration_date, status)
                    VALUES (?, ?, ?, 'registered');
                """, (user_id, event_id, reg_date_str))
                return True, f"Successfully registered for '{event['title']}'!"

    except sqlite3.IntegrityError as e:
        return False, f"Registration conflict: {str(e)}"
    except sqlite3.Error as e:
        return False, f"Database error during registration: {str(e)}"
    finally:
        conn.close()


def cancel_registration(registration_id: int, current_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Cancels an active registration by updating status to 'cancelled'.
    Students can only cancel their own registrations. Admins can cancel any.
    """
    if not current_user:
        return False, "Authentication required."

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.registration_id, r.user_id, r.status, e.title
            FROM registrations r
            JOIN events e ON r.event_id = e.event_id
            WHERE r.registration_id = ?;
        """, (registration_id,))
        reg = cursor.fetchone()

        if not reg:
            return False, "Registration record not found."

        # Permission check: student cannot cancel someone else's registration
        if current_user.get("role") == "student" and reg["user_id"] != current_user.get("user_id"):
            return False, "Permission denied: You can only cancel your own registrations."

        if reg["status"] == "cancelled":
            return False, "This registration is already cancelled."

        cursor.execute("""
            UPDATE registrations
            SET status = 'cancelled'
            WHERE registration_id = ?;
        """, (registration_id,))
        conn.commit()
        return True, f"Registration for '{reg['title']}' has been cancelled."
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_student_registrations(user_id: int, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetches all registrations for a specific student.
    Enforces that students can only view their own registrations.
    """
    if not current_user:
        return []

    # Student cannot view other students' registrations
    if current_user.get("role") == "student" and current_user.get("user_id") != user_id:
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                r.registration_id,
                r.user_id,
                r.event_id,
                r.registration_date,
                r.status,
                e.title AS event_title,
                e.category,
                e.event_date,
                e.venue,
                e.fee
            FROM registrations r
            JOIN events e ON r.event_id = e.event_id
            WHERE r.user_id = ?
            ORDER BY e.event_date ASC, r.registration_date DESC;
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_all_registrations(search_query: Optional[str] = None,
                          event_id_filter: Optional[int] = None,
                          admin_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Fetches all registration records across students and events.
    Restricted to admin role only. Supports search and event filter.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        base_query = """
            SELECT 
                r.registration_id,
                r.user_id,
                r.event_id,
                r.registration_date,
                r.status,
                u.full_name AS student_name,
                u.roll_no,
                u.department,
                u.email,
                e.title AS event_title,
                e.category,
                e.event_date,
                e.venue
            FROM registrations r
            JOIN users u ON r.user_id = u.user_id
            JOIN events e ON r.event_id = e.event_id
            WHERE 1=1
        """
        params = []

        if event_id_filter and event_id_filter > 0:
            base_query += " AND r.event_id = ?"
            params.append(event_id_filter)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            base_query += " AND (u.full_name LIKE ? OR u.roll_no LIKE ? OR e.title LIKE ?)"
            params.extend([term, term, term])

        base_query += " ORDER BY r.registration_date DESC;"
        cursor.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_dashboard_stats(admin_user: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculates actual database statistics for the admin dashboard.
    Enforces admin-only access.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return {"total_events": 0, "total_students": 0, "active_registrations": 0, "upcoming_events": 0}

    today_str = date.today().isoformat()
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS count FROM events;")
        total_events = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student';")
        total_students = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM registrations WHERE status = 'registered';")
        active_registrations = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM events WHERE event_date >= ?;", (today_str,))
        upcoming_events = cursor.fetchone()["count"]

        return {
            "total_events": total_events,
            "total_students": total_students,
            "active_registrations": active_registrations,
            "upcoming_events": upcoming_events
        }
    finally:
        conn.close()
