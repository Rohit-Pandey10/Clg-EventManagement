"""
services/event_service.py
Service handling all business logic, validation, and database operations for Events.
Role enforcement: Only 'admin' users can create, update, or delete events.
"""

from datetime import datetime, date
import sqlite3
from typing import List, Dict, Any, Tuple, Optional
from database import get_connection

CATEGORIES = ["Technical", "Cultural", "Sports", "Workshop", "Seminar", "Other"]


def validate_event_data(title: str, category: str, event_date_str: str,
                        venue: str, fee_str: str, capacity_str: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates form data for adding or updating an event.
    Returns (is_valid, error_message, parsed_data_dict).
    """
    clean_title = title.strip()
    clean_category = category.strip()
    clean_date = event_date_str.strip()
    clean_venue = venue.strip()

    if not clean_title:
        return False, "Event title cannot be empty.", {}
    if not clean_category:
        return False, "Please select an event category.", {}
    if not clean_venue:
        return False, "Venue cannot be empty.", {}

    # Validate date format (YYYY-MM-DD)
    try:
        parsed_date = datetime.strptime(clean_date, "%Y-%m-%d").date()
    except ValueError:
        return False, "Invalid date format. Please use YYYY-MM-DD.", {}

    # Validate fee
    try:
        clean_fee = float(fee_str.strip() if fee_str else "0")
        if clean_fee < 0:
            return False, "Event fee cannot be negative.", {}
    except ValueError:
        return False, "Event fee must be a valid number.", {}

    # Validate capacity
    try:
        clean_capacity = int(capacity_str.strip())
        if clean_capacity <= 0:
            return False, "Event capacity must be greater than zero.", {}
    except ValueError:
        return False, "Capacity must be a positive integer.", {}

    return True, "", {
        "title": clean_title,
        "category": clean_category,
        "event_date": parsed_date.strftime("%Y-%m-%d"),
        "venue": clean_venue,
        "fee": clean_fee,
        "capacity": clean_capacity
    }


def create_event(title: str, category: str, event_date_str: str, venue: str,
                 description: str, fee_str: str, capacity_str: str,
                 admin_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Creates a new event. Role permission check: must be admin.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return False, "Permission denied: Only administrators can create events."

    is_valid, err_msg, data = validate_event_data(title, category, event_date_str, venue, fee_str, capacity_str)
    if not is_valid:
        return False, err_msg

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO events (title, category, event_date, venue, description, fee, capacity, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            data["title"],
            data["category"],
            data["event_date"],
            data["venue"],
            description.strip(),
            data["fee"],
            data["capacity"],
            admin_user.get("user_id")
        ))
        conn.commit()
        return True, "Event created successfully!"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error creating event: {str(e)}"
    finally:
        conn.close()


def update_event(event_id: int, title: str, category: str, event_date_str: str,
                 venue: str, description: str, fee_str: str, capacity_str: str,
                 admin_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Updates an existing event.
    Enforces that capacity cannot be reduced below current active registrations.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return False, "Permission denied: Only administrators can update events."

    is_valid, err_msg, data = validate_event_data(title, category, event_date_str, venue, fee_str, capacity_str)
    if not is_valid:
        return False, err_msg

    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Check active registrations count
        cursor.execute("""
            SELECT COUNT(*) AS active_count
            FROM registrations
            WHERE event_id = ? AND status = 'registered';
        """, (event_id,))
        active_count = cursor.fetchone()["active_count"]

        if data["capacity"] < active_count:
            return False, f"Capacity ({data['capacity']}) cannot be less than active registrations ({active_count})."

        cursor.execute("""
            UPDATE events
            SET title = ?, category = ?, event_date = ?, venue = ?, description = ?, fee = ?, capacity = ?
            WHERE event_id = ?;
        """, (
            data["title"],
            data["category"],
            data["event_date"],
            data["venue"],
            description.strip(),
            data["fee"],
            data["capacity"],
            event_id
        ))
        conn.commit()
        return True, "Event updated successfully!"
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error updating event: {str(e)}"
    finally:
        conn.close()


def delete_event(event_id: int, admin_user: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deletes an event. Prevents accidental deletion if there are active registrations.
    """
    if not admin_user or admin_user.get("role") != "admin":
        return False, "Permission denied: Only administrators can delete events."

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) AS active_count
            FROM registrations
            WHERE event_id = ? AND status = 'registered';
        """, (event_id,))
        active_count = cursor.fetchone()["active_count"]

        if active_count > 0:
            return False, f"Cannot delete event: There are {active_count} active student registration(s)."

        cursor.execute("DELETE FROM events WHERE event_id = ?;", (event_id,))
        conn.commit()
        return True, "Event deleted successfully."
    except sqlite3.Error as e:
        conn.rollback()
        return False, f"Database error deleting event: {str(e)}"
    finally:
        conn.close()


def get_all_events(search_query: Optional[str] = None, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches all events with registered student counts and available seats.
    Can be filtered by search query (title or venue) and category.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        base_query = """
            SELECT 
                e.event_id,
                e.title,
                e.category,
                e.event_date,
                e.venue,
                e.description,
                e.fee,
                e.capacity,
                e.created_by,
                COALESCE(reg.active_count, 0) AS registered_count,
                (e.capacity - COALESCE(reg.active_count, 0)) AS available_seats
            FROM events e
            LEFT JOIN (
                SELECT event_id, COUNT(*) AS active_count
                FROM registrations
                WHERE status = 'registered'
                GROUP BY event_id
            ) reg ON e.event_id = reg.event_id
            WHERE 1=1
        """
        params = []

        if search_query and search_query.strip():
            clean_search = f"%{search_query.strip()}%"
            base_query += " AND (e.title LIKE ? OR e.venue LIKE ? OR e.description LIKE ?)"
            params.extend([clean_search, clean_search, clean_search])

        if category_filter and category_filter.strip() and category_filter != "All":
            base_query += " AND e.category = ?"
            params.append(category_filter.strip())

        base_query += " ORDER BY e.event_date ASC, e.title ASC;"
        cursor.execute(base_query, params)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_upcoming_events(search_query: Optional[str] = None, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches events scheduled for today or in the future.
    Used on student and admin dashboards.
    """
    today_str = date.today().isoformat()
    conn = get_connection()
    try:
        cursor = conn.cursor()
        base_query = """
            SELECT 
                e.event_id,
                e.title,
                e.category,
                e.event_date,
                e.venue,
                e.description,
                e.fee,
                e.capacity,
                COALESCE(reg.active_count, 0) AS registered_count,
                (e.capacity - COALESCE(reg.active_count, 0)) AS available_seats
            FROM events e
            LEFT JOIN (
                SELECT event_id, COUNT(*) AS active_count
                FROM registrations
                WHERE status = 'registered'
                GROUP BY event_id
            ) reg ON e.event_id = reg.event_id
            WHERE e.event_date >= ?
        """
        params = [today_str]

        if search_query and search_query.strip():
            clean_search = f"%{search_query.strip()}%"
            base_query += " AND (e.title LIKE ? OR e.venue LIKE ?)"
            params.extend([clean_search, clean_search])

        if category_filter and category_filter.strip() and category_filter != "All":
            base_query += " AND e.category = ?"
            params.append(category_filter.strip())

        base_query += " ORDER BY e.event_date ASC;"
        cursor.execute(base_query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
    """Fetches full details of a specific event."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.*,
                COALESCE(reg.active_count, 0) AS registered_count,
                (e.capacity - COALESCE(reg.active_count, 0)) AS available_seats
            FROM events e
            LEFT JOIN (
                SELECT event_id, COUNT(*) AS active_count
                FROM registrations
                WHERE status = 'registered'
                GROUP BY event_id
            ) reg ON e.event_id = reg.event_id
            WHERE e.event_id = ?;
        """, (event_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
