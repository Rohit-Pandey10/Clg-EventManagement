from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import User, Event, Registration


class CEMSTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.localdate()

        # Create Admin User
        self.admin = User.objects.create_user(
            username="admin",
            password="adminpassword",
            full_name="Administrator",
            role="admin",
            department="Admin Dept",
            email="admin@test.edu",
            is_staff=True
        )

        # Create Students
        self.student1 = User.objects.create_user(
            username="student1",
            password="studentpassword",
            full_name="Alice Smith",
            roll_no="R001",
            department="Computer Science",
            email="alice@test.edu",
            role="student"
        )

        self.student2 = User.objects.create_user(
            username="student2",
            password="studentpassword",
            full_name="Bob Jones",
            roll_no="R002",
            department="Mechanical",
            email="bob@test.edu",
            role="student"
        )

        # Create Upcoming Event with capacity = 2
        self.upcoming_event = Event.objects.create(
            title="Tech Hackathon 2026",
            category="Technical",
            event_date=self.today + timedelta(days=7),
            venue="Main Lab",
            description="24-hour coding challenge",
            fee=0.00,
            capacity=2,
            created_by=self.admin
        )

        # Create Past Event
        self.past_event = Event.objects.create(
            title="Past Robotics Workshop",
            category="Workshop",
            event_date=self.today - timedelta(days=5),
            venue="Robotics Hall",
            description="Old workshop",
            fee=50.00,
            capacity=20,
            created_by=self.admin
        )

    def test_01_user_roles_and_properties(self):
        self.assertTrue(self.admin.is_cems_admin)
        self.assertFalse(self.admin.is_cems_student)
        self.assertTrue(self.student1.is_cems_student)
        self.assertFalse(self.student1.is_cems_admin)
        self.assertEqual(self.student1.roll_no, "R001")

    def test_02_event_capacity_and_seat_tracking(self):
        self.assertEqual(self.upcoming_event.capacity, 2)
        self.assertEqual(self.upcoming_event.active_registrations_count, 0)
        self.assertEqual(self.upcoming_event.available_seats, 2)
        self.assertFalse(self.upcoming_event.is_full)
        self.assertFalse(self.upcoming_event.is_past)
        self.assertTrue(self.past_event.is_past)

    def test_03_admin_access_control(self):
        # Anonymous cannot access admin dashboard
        res = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(res.status_code, 302)

        # Student cannot access admin dashboard
        self.client.login(username="student1", password="studentpassword")
        res = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(res.status_code, 302)
        self.client.logout()

        # Admin can access admin dashboard
        self.client.login(username="admin", password="adminpassword")
        res = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Dashboard Overview")

    def test_04_student_portal_access(self):
        self.client.login(username="student1", password="studentpassword")
        res = self.client.get(reverse("student_dashboard"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Welcome, Alice Smith!")

        # Browse events
        res = self.client.get(reverse("browse_events"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Tech Hackathon 2026")

    def test_05_event_registration_flow_and_capacity_limits(self):
        self.client.login(username="student1", password="studentpassword")

        # Student 1 registers for upcoming event
        res = self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.upcoming_event.active_registrations_count, 1)
        self.assertEqual(self.upcoming_event.available_seats, 1)
        self.client.logout()

        # Student 2 registers for upcoming event (now at max capacity = 2)
        self.client.login(username="student2", password="studentpassword")
        res = self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.upcoming_event.active_registrations_count, 2)
        self.assertEqual(self.upcoming_event.available_seats, 0)
        self.assertTrue(self.upcoming_event.is_full)
        self.client.logout()

        # Student 3 tries to register when event is full
        student3 = User.objects.create_user(
            username="student3",
            password="studentpassword",
            full_name="Charlie Brown",
            roll_no="R003",
            role="student"
        )
        self.client.login(username="student3", password="studentpassword")
        res = self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        self.assertEqual(res.status_code, 302)
        # Count still remains 2
        self.assertEqual(self.upcoming_event.active_registrations_count, 2)
        self.assertFalse(Registration.objects.filter(user=student3, event=self.upcoming_event).exists())

    def test_06_cancellation_and_reactivation(self):
        # Student 1 registers
        self.client.login(username="student1", password="studentpassword")
        self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        reg = Registration.objects.get(user=self.student1, event=self.upcoming_event)
        self.assertEqual(reg.status, "registered")

        # Student 1 cancels
        res = self.client.post(reverse("cancel_registration", args=[reg.id]))
        self.assertEqual(res.status_code, 302)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "cancelled")
        self.assertEqual(self.upcoming_event.active_registrations_count, 0)

        # Student 1 reactivates registration
        res = self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        self.assertEqual(res.status_code, 302)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "registered")
        self.assertEqual(self.upcoming_event.active_registrations_count, 1)

    def test_07_past_event_registration_blocked(self):
        self.client.login(username="student1", password="studentpassword")
        res = self.client.post(reverse("register_event", args=[self.past_event.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Registration.objects.filter(user=self.student1, event=self.past_event).exists())

    def test_08_event_deletion_blocked_with_active_registrations(self):
        self.client.login(username="student1", password="studentpassword")
        self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        self.client.logout()

        self.client.login(username="admin", password="adminpassword")
        # Try to delete event that has active registrations
        res = self.client.post(reverse("event_delete", args=[self.upcoming_event.id]))
        self.assertEqual(res.status_code, 302)
        # Event must still exist in DB
        self.assertTrue(Event.objects.filter(id=self.upcoming_event.id).exists())

    def test_09_cancellation_post_vs_get_and_seat_count_update(self):
        self.client.login(username="student1", password="studentpassword")
        # Register for upcoming event
        self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        reg = Registration.objects.get(user=self.student1, event=self.upcoming_event)
        self.assertEqual(reg.status, "registered")
        self.assertEqual(self.upcoming_event.active_registrations_count, 1)
        self.assertEqual(self.upcoming_event.available_seats, 1)

        # 1. GET to cancel_registration must NOT cancel the registration
        res_get = self.client.get(reverse("cancel_registration", args=[reg.id]))
        self.assertEqual(res_get.status_code, 302)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "registered")
        self.assertEqual(self.upcoming_event.active_registrations_count, 1)

        # 2. POST to cancel_registration must cancel the registration and update seat count
        res_post = self.client.post(reverse("cancel_registration", args=[reg.id]), follow=True)
        self.assertEqual(res_post.status_code, 200)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "cancelled")
        self.assertEqual(self.upcoming_event.active_registrations_count, 0)
        self.assertEqual(self.upcoming_event.available_seats, 2)
        self.assertContains(res_post, f"Registration cancelled for {self.upcoming_event.title}.")

    def test_10_student_cannot_cancel_other_student_registration(self):
        # Student 1 registers for upcoming event
        self.client.login(username="student1", password="studentpassword")
        self.client.post(reverse("register_event", args=[self.upcoming_event.id]))
        reg1 = Registration.objects.get(user=self.student1, event=self.upcoming_event)
        self.assertEqual(reg1.status, "registered")
        self.client.logout()

        # Student 2 logs in and attempts to POST to cancel Student 1's registration
        self.client.login(username="student2", password="studentpassword")
        res = self.client.post(reverse("cancel_registration", args=[reg1.id]))
        self.assertIn(res.status_code, [403, 302])
        reg1.refresh_from_db()
        self.assertEqual(reg1.status, "registered")
        self.client.logout()

        # Student 1 logs in and cancels their own registration -> status becomes 'cancelled'
        self.client.login(username="student1", password="studentpassword")
        res_own = self.client.post(reverse("cancel_registration", args=[reg1.id]))
        self.assertEqual(res_own.status_code, 302)
        reg1.refresh_from_db()
        self.assertEqual(reg1.status, "cancelled")

    def test_11_student_blocked_from_all_admin_urls(self):
        self.client.login(username="student1", password="studentpassword")
        admin_urls = [
            reverse("admin_dashboard"),
            reverse("event_list"),
            reverse("event_create"),
            reverse("student_list"),
            reverse("student_create"),
            reverse("registration_list"),
        ]
        for url in admin_urls:
            res = self.client.get(url)
            self.assertIn(res.status_code, [302, 403])
