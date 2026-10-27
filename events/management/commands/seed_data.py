from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from events.models import Event, Registration

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with initial administrators, students, realistic events, and registrations."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Starting CEMS database seeding..."))

        # 1. Create or get Admin
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "full_name": "System Administrator",
                "department": "Administration",
                "email": "admin@college.edu",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
            }
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  [+] Admin created: admin / admin123"))
        else:
            if admin.role != "admin" or not admin.is_staff or not admin.is_superuser:
                admin.role = "admin"
                admin.is_staff = True
                admin.is_superuser = True
                admin.save()
            self.stdout.write(self.style.WARNING("  [~] Admin already exists."))

        # 2. Create Students
        students_data = [
            {
                "username": "alice",
                "password": "password123",
                "full_name": "Alice Sharma",
                "roll_no": "CS2026-001",
                "department": "Computer Engineering",
                "email": "alice@college.edu",
            },
            {
                "username": "bob",
                "password": "password123",
                "full_name": "Bob Patel",
                "roll_no": "IT2026-014",
                "department": "Information Technology",
                "email": "bob@college.edu",
            },
            {
                "username": "charlie",
                "password": "password123",
                "full_name": "Charlie Gupta",
                "roll_no": "AI2026-022",
                "department": "Artificial Intelligence & Data Science",
                "email": "charlie@college.edu",
            },
            {
                "username": "diana",
                "password": "password123",
                "full_name": "Diana Dsouza",
                "roll_no": "EXTC2026-035",
                "department": "Electronics & Telecommunication",
                "email": "diana@college.edu",
            },
        ]

        students_map = {}
        for s in students_data:
            student, s_created = User.objects.get_or_create(
                username=s["username"],
                defaults={
                    "full_name": s["full_name"],
                    "roll_no": s["roll_no"],
                    "department": s["department"],
                    "email": s["email"],
                    "role": "student",
                }
            )
            if s_created:
                student.set_password(s["password"])
                student.save()
                self.stdout.write(self.style.SUCCESS(f"  [+] Student created: {student.username} / {s['password']}"))
            students_map[s["username"]] = student

        # 3. Create Events
        today = timezone.localdate()
        events_data = [
            {
                "title": "AI & Machine Learning 24h Hackathon",
                "category": "Technical",
                "event_date": today + timedelta(days=10),
                "venue": "Main Turing Auditorium & Lab 401",
                "description": "24-hour flagship hackathon solving real-world challenges in GenAI, autonomous systems, and edge computing. Catering, Wi-Fi, and mentor support provided.",
                "fee": 0.00,
                "capacity": 60,
            },
            {
                "title": "Aura 2026: Annual Cultural Fiesta",
                "category": "Cultural",
                "event_date": today + timedelta(days=18),
                "venue": "Open Air Amphitheatre",
                "description": "The campus's biggest cultural extravaganza featuring music battles, classical and modern dance competitions, theatrical plays, and star evening shows.",
                "fee": 150.00,
                "capacity": 150,
            },
            {
                "title": "Inter-College 7-a-Side Football Cup",
                "category": "Sports",
                "event_date": today + timedelta(days=25),
                "venue": "University Sports Complex Turf",
                "description": "High-octane knockouts with teams from across state colleges. Official referees, live commentary, trophies, and cash prizes for champions.",
                "fee": 50.00,
                "capacity": 80,
            },
            {
                "title": "Cloud Native & DevOps Hands-on Bootcamp",
                "category": "Workshop",
                "event_date": today + timedelta(days=14),
                "venue": "Seminar Hall B & Hybrid Live Stream",
                "description": "Deep-dive workshop on Docker containers, Kubernetes orchestrations, Terraform infrastructure-as-code, and GitHub Actions CI/CD pipelines.",
                "fee": 99.00,
                "capacity": 45,
            },
            {
                "title": "Big Tech Career & System Design Seminar",
                "category": "Seminar",
                "event_date": today + timedelta(days=32),
                "venue": "Executive Conference Hall 1",
                "description": "Alumni keynote speakers from Google, Microsoft, and Uber discussing technical interviews, scalable system design, and open-source contributions.",
                "fee": 0.00,
                "capacity": 120,
            },
            {
                "title": "Autonomous Drone & Robotics Expo (Past Edition)",
                "category": "Workshop",
                "event_date": today - timedelta(days=20),
                "venue": "Robotics Lab & Indoor Field",
                "description": "Hands-on flight controller programming and autonomous navigation demo. Successfully concluded with student showcase.",
                "fee": 120.00,
                "capacity": 40,
            },
        ]

        events_map = {}
        for ev in events_data:
            event, e_created = Event.objects.get_or_create(
                title=ev["title"],
                defaults={
                    "category": ev["category"],
                    "event_date": ev["event_date"],
                    "venue": ev["venue"],
                    "description": ev["description"],
                    "fee": ev["fee"],
                    "capacity": ev["capacity"],
                    "created_by": admin,
                }
            )
            if e_created:
                self.stdout.write(self.style.SUCCESS(f"  [+] Event created: '{event.title}'"))
            events_map[ev["title"]] = event

        # 4. Create Registrations
        sample_regs = [
            ("alice", "AI & Machine Learning 24h Hackathon", "registered"),
            ("alice", "Cloud Native & DevOps Hands-on Bootcamp", "registered"),
            ("bob", "AI & Machine Learning 24h Hackathon", "registered"),
            ("bob", "Aura 2026: Annual Cultural Fiesta", "registered"),
            ("charlie", "AI & Machine Learning 24h Hackathon", "registered"),
            ("charlie", "Inter-College 7-a-Side Football Cup", "registered"),
            ("charlie", "Cloud Native & DevOps Hands-on Bootcamp", "cancelled"),
            ("diana", "Aura 2026: Annual Cultural Fiesta", "registered"),
            ("diana", "Big Tech Career & System Design Seminar", "registered"),
            ("alice", "Autonomous Drone & Robotics Expo (Past Edition)", "registered"),
        ]

        for username, event_title, status in sample_regs:
            u = students_map.get(username)
            e = events_map.get(event_title)
            if u and e:
                reg, r_created = Registration.objects.get_or_create(
                    user=u,
                    event=e,
                    defaults={"status": status}
                )
                if r_created:
                    self.stdout.write(self.style.SUCCESS(f"  [+] Registration: {username} -> {event_title} ({status})"))

        self.stdout.write(self.style.SUCCESS("✅ Database seeding completed successfully!"))

