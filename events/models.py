from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import date


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin / Organizer"),
        ("student", "Student"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")
    full_name = models.CharField(max_length=150, blank=True)
    roll_no = models.CharField(max_length=50, blank=True, null=True, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        elif self.full_name and not self.first_name:
            parts = self.full_name.split(maxsplit=1)
            self.first_name = parts[0]
            if len(parts) > 1:
                self.last_name = parts[1]
        if self.is_superuser or self.is_staff:
            self.role = "admin"
        if self.roll_no:
            self.roll_no = self.roll_no.strip().upper()
        super().save(*args, **kwargs)

    @property
    def is_cems_admin(self) -> bool:
        return self.role == "admin" or self.is_staff or self.is_superuser

    @property
    def is_cems_student(self) -> bool:
        return self.role == "student"

    def __str__(self):
        display = self.full_name or self.username
        if self.roll_no:
            return f"{display} ({self.roll_no})"
        return f"{display} [{self.get_role_display()}]"


class Event(models.Model):
    CATEGORY_CHOICES = [
        ("Technical", "Technical"),
        ("Cultural", "Cultural"),
        ("Sports", "Sports"),
        ("Workshop", "Workshop"),
        ("Seminar", "Seminar"),
        ("Other", "Other"),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    event_date = models.DateField()
    venue = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    capacity = models.PositiveIntegerField(default=50)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date", "title"]

    def __str__(self):
        return f"{self.title} ({self.event_date.strftime('%Y-%m-%d')})"

    @property
    def active_registrations_count(self) -> int:
        return self.registrations.filter(status="registered").count()

    @property
    def available_seats(self) -> int:
        return max(0, self.capacity - self.active_registrations_count)

    @property
    def is_full(self) -> bool:
        return self.available_seats <= 0

    @property
    def is_past(self) -> bool:
        return self.event_date < timezone.localdate()

    @property
    def seat_percentage(self) -> int:
        if self.capacity <= 0:
            return 100
        return min(100, int((self.active_registrations_count / self.capacity) * 100))


class Registration(models.Model):
    STATUS_CHOICES = [
        ("registered", "Registered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="registered")

    class Meta:
        unique_together = ("user", "event")
        ordering = ["-registration_date"]

    def __str__(self):
        return f"{self.user.username} -> {self.event.title} [{self.status}]"
