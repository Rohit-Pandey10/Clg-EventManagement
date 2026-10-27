from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Event, Registration


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("CEMS Profile", {"fields": ("role", "full_name", "roll_no", "department")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("CEMS Profile", {"fields": ("role", "full_name", "roll_no", "department", "email")}),
    )
    list_display = ("username", "full_name", "roll_no", "role", "department", "email", "is_staff")
    list_filter = ("role", "department", "is_staff", "is_superuser")
    search_fields = ("username", "full_name", "roll_no", "email")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "event_date", "venue", "fee", "capacity", "active_registrations_count", "created_by")
    list_filter = ("category", "event_date")
    search_fields = ("title", "venue", "description")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "registration_date", "status")
    list_filter = ("status", "registration_date", "event__category")
    search_fields = ("user__username", "user__full_name", "user__roll_no", "event__title")
