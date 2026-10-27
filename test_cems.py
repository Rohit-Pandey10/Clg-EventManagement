"""
test_cems.py
Automated test suite verifying the business logic, security constraints,
database operations, and role enforcement for College Event Management System.
"""

import os
import sys
import unittest
from datetime import date, timedelta

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import init_db, get_connection, DB_FILE
from auth import hash_password, verify_password, authenticate_user
from services.event_service import (
    create_event,
    update_event,
    delete_event,
    get_all_events,
    get_upcoming_events,
    get_event_by_id
)
from services.student_service import (
    create_student,
    update_student,
    get_all_students,
    get_student_by_id
)
from services.registration_service import (
    register_for_event,
    cancel_registration,
    get_student_registrations,
    get_all_registrations,
    get_dashboard_stats
)


class TestCEMS(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Fresh test database
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        init_db(default_admin_password="admin123")

    def setUp(self):
        # Fetch admin user
        user, _ = authenticate_user("admin", "admin123", get_connection)
        self.assertIsNotNone(user)
        self.admin_user = user

    def test_01_admin_login_success_and_failure(self):
        # Valid login
        user, msg = authenticate_user("admin", "admin123", get_connection)
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "admin")
        self.assertEqual(user["username"], "admin")

        # Invalid password
        user_fail, msg_fail = authenticate_user("admin", "wrongpass", get_connection)
        self.assertIsNone(user_fail)

        # Invalid username
        user_fail2, msg_fail2 = authenticate_user("nonexistent", "admin123", get_connection)
        self.assertIsNone(user_fail2)

    def test_02_create_and_manage_students(self):
        # Admin creates student 1
        ok, msg = create_student(
            full_name="Alice Sharma",
            username="alice",
            password="password123",
            roll_no="R101",
            department="Computer Engineering",
            email="alice@college.edu",
            admin_user=self.admin_user
        )
        self.assertTrue(ok, msg)

        # Admin creates student 2
        ok, msg = create_student(
            full_name="Bob Patel",
            username="bob",
            password="password123",
            roll_no="R102",
            department="Information Technology",
            email="bob@college.edu",
            admin_user=self.admin_user
        )
        self.assertTrue(ok, msg)

        # Student login check
        alice_user, _ = authenticate_user("alice", "password123", get_connection)
        self.assertIsNotNone(alice_user)
        self.assertEqual(alice_user["role"], "student")
        self.assertEqual(alice_user["roll_no"], "R101")

        # Test duplicate username rejection
        ok_dup_user, msg_dup_user = create_student(
            full_name="Alice Duplicate",
            username="alice",
            password="pass",
            roll_no="R999",
            department="CE",
            email="other@college.edu",
            admin_user=self.admin_user
        )
        self.assertFalse(ok_dup_user)
        self.assertIn("already taken", msg_dup_user.lower())

        # Test duplicate roll number rejection
        ok_dup_roll, msg_dup_roll = create_student(
            full_name="Charlie",
            username="charlie",
            password="pass",
            roll_no="R101",
            department="CE",
            email="charlie@college.edu",
            admin_user=self.admin_user
        )
        self.assertFalse(ok_dup_roll)
        self.assertIn("already registered", msg_dup_roll.lower())

        # Test student role rejection when non-admin attempts to create student
        ok_forbidden, msg_forbidden = create_student(
            full_name="Dave",
            username="dave",
            password="pass",
            roll_no="R103",
            department="CE",
            email="dave@college.edu",
            admin_user=alice_user  # Student trying to create student
        )
        self.assertFalse(ok_forbidden)
        self.assertIn("denied", msg_forbidden.lower())

    def test_03_event_crud_and_validations(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        # Add event with invalid date
        ok, msg = create_event(
            title="Bad Date Event",
            category="Technical",
            event_date_str="2026/13/45",
            venue="Auditorium",
            description="Test",
            fee_str="0",
            capacity_str="10",
            admin_user=self.admin_user
        )
        self.assertFalse(ok)
        self.assertIn("format", msg.lower())

        # Add event with negative fee
        ok, msg = create_event(
            title="Negative Fee Event",
            category="Technical",
            event_date_str=tomorrow,
            venue="Auditorium",
            description="Test",
            fee_str="-50",
            capacity_str="10",
            admin_user=self.admin_user
        )
        self.assertFalse(ok)
        self.assertIn("negative", msg.lower())

        # Add event with non-positive capacity
        ok, msg = create_event(
            title="Zero Capacity Event",
            category="Technical",
            event_date_str=tomorrow,
            venue="Auditorium",
            description="Test",
            fee_str="100",
            capacity_str="0",
            admin_user=self.admin_user
        )
        self.assertFalse(ok)
        self.assertIn("greater than zero", msg.lower())

        # Create valid event with capacity 1 (to test full capacity later)
        ok, msg = create_event(
            title="Hackathon 2026",
            category="Technical",
            event_date_str=tomorrow,
            venue="Seminar Hall 1",
            description="Annual coding competition",
            fee_str="50.0",
            capacity_str="1",
            admin_user=self.admin_user
        )
        self.assertTrue(ok, msg)

        # Retrieve event
        events = get_all_events(search_query="Hackathon")
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["title"], "Hackathon 2026")
        self.assertEqual(event["capacity"], 1)
        self.assertEqual(event["available_seats"], 1)

    def test_04_registration_capacity_and_cancellation(self):
        events = get_all_events(search_query="Hackathon")
        event = events[0]
        event_id = event["event_id"]

        alice_user, _ = authenticate_user("alice", "password123", get_connection)
        bob_user, _ = authenticate_user("bob", "password123", get_connection)

        # 1. Alice registers successfully
        ok, msg = register_for_event(alice_user["user_id"], event_id, alice_user)
        self.assertTrue(ok, msg)

        # 2. Duplicate registration attempt by Alice
        ok_dup, msg_dup = register_for_event(alice_user["user_id"], event_id, alice_user)
        self.assertFalse(ok_dup)
        self.assertIn("already registered", msg_dup.lower())

        # 3. Bob attempts to register when event is full (capacity = 1)
        ok_full, msg_full = register_for_event(bob_user["user_id"], event_id, bob_user)
        self.assertFalse(ok_full)
        self.assertIn("full", msg_full.lower())

        # 4. Check available seats = 0
        ev_after = get_event_by_id(event_id)
        self.assertEqual(ev_after["available_seats"], 0)
        self.assertEqual(ev_after["registered_count"], 1)

        # 5. Cannot reduce capacity below active registrations
        ok_upd, msg_upd = update_event(
            event_id=event_id,
            title="Hackathon 2026",
            category="Technical",
            event_date_str=event["event_date"],
            venue="Seminar Hall 1",
            description="Updated desc",
            fee_str="50",
            capacity_str="0",
            admin_user=self.admin_user
        )
        self.assertFalse(ok_upd)

        # 6. Cannot delete event with active registrations
        ok_del, msg_del = delete_event(event_id, self.admin_user)
        self.assertFalse(ok_del)
        self.assertIn("active student registration", msg_del.lower())

        # 7. Alice cancels registration
        alice_regs = get_student_registrations(alice_user["user_id"], alice_user)
        self.assertEqual(len(alice_regs), 1)
        reg_id = alice_regs[0]["registration_id"]

        ok_cancel, msg_cancel = cancel_registration(reg_id, alice_user)
        self.assertTrue(ok_cancel, msg_cancel)

        # 8. Available seats restored to 1
        ev_cancelled = get_event_by_id(event_id)
        self.assertEqual(ev_cancelled["available_seats"], 1)
        self.assertEqual(ev_cancelled["registered_count"], 0)

        # 9. Bob can now register
        ok_bob, msg_bob = register_for_event(bob_user["user_id"], event_id, bob_user)
        self.assertTrue(ok_bob, msg_bob)

        # 10. Check student isolation: Alice cannot view Bob's registrations
        bobs_regs_as_alice = get_student_registrations(bob_user["user_id"], alice_user)
        self.assertEqual(len(bobs_regs_as_alice), 0)

        # 11. Admin can view all registrations
        all_regs = get_all_registrations(admin_user=self.admin_user)
        self.assertEqual(len(all_regs), 2)  # Alice (cancelled) + Bob (registered)

    def test_05_past_event_registration_rejection(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        ok, msg = create_event(
            title="Old Past Workshop",
            category="Workshop",
            event_date_str=yesterday,
            venue="Lab 4",
            description="Past event",
            fee_str="0",
            capacity_str="20",
            admin_user=self.admin_user
        )
        self.assertTrue(ok)

        past_events = get_all_events(search_query="Old Past")
        past_id = past_events[0]["event_id"]

        alice_user, _ = authenticate_user("alice", "password123", get_connection)
        ok_reg, msg_reg = register_for_event(alice_user["user_id"], past_id, alice_user)
        self.assertFalse(ok_reg)
        self.assertIn("past", msg_reg.lower())

    def test_06_dashboard_statistics(self):
        stats = get_dashboard_stats(self.admin_user)
        self.assertGreaterEqual(stats["total_events"], 2)
        self.assertGreaterEqual(stats["total_students"], 2)
        self.assertGreaterEqual(stats["active_registrations"], 1)


if __name__ == "__main__":
    unittest.main()
