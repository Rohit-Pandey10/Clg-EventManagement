from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponseForbidden, JsonResponse
from datetime import date

from .models import Event, Registration
from .forms import (
    LoginForm,
    EventForm,
    StudentCreationForm,
    StudentUpdateForm,
    StudentRegisterForm,
)

User = get_user_model()


def admin_required(view_func):
    """Decorator ensuring the logged in user has Admin / Organizer privileges."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please sign in to access the administrator portal.")
            return redirect("login")
        if not request.user.is_cems_admin:
            messages.error(request, "Permission denied: Administrator privileges required.")
            return redirect("student_dashboard")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    """Decorator ensuring the logged in user is a student."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please sign in to access the student portal.")
            return redirect("login")
        if request.user.is_cems_admin:
            # Admins can be redirected to admin dashboard
            messages.info(request, "Administrators operate from the Organizer Dashboard.")
            return redirect("admin_dashboard")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==============================================================================
# Authentication & Root Router Views
# ==============================================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.full_name or user.username}!")
                next_url = request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(next_url)
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        name = request.user.full_name or request.user.username
        logout(request)
        messages.info(request, f"You have been successfully signed out. Goodbye, {name}!")
    return redirect("login")


def register_student_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                full_name=form.cleaned_data["full_name"],
                roll_no=form.cleaned_data["roll_no"],
                department=form.cleaned_data["department"],
                email=form.cleaned_data["email"],
                role="student"
            )
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome to CEMS, {user.full_name}!")
            return redirect("student_dashboard")
        else:
            messages.error(request, "Please correct the errors indicated below.")
    else:
        form = StudentRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard_view(request):
    if request.user.is_cems_admin:
        return redirect("admin_dashboard")
    return redirect("student_dashboard")


# ==============================================================================
# Administrator Portal Views
# ==============================================================================

@admin_required
def admin_dashboard(request):
    today = timezone.localdate()
    total_events = Event.objects.count()
    total_students = User.objects.filter(role="student").count()
    active_registrations = Registration.objects.filter(status="registered").count()
    upcoming_events_count = Event.objects.filter(event_date__gte=today).count()

    upcoming_events = Event.objects.filter(event_date__gte=today).order_by("event_date")[:6]
    recent_registrations = Registration.objects.select_related("user", "event").order_by("-registration_date")[:8]

    total_capacity = Event.objects.aggregate(total=models.Sum("capacity"))["total"] or 0
    seats_filled_percent = min(100, int((active_registrations / total_capacity * 100))) if total_capacity > 0 else 0
    events_by_popularity = Event.objects.annotate(
        active_count=Count("registrations", filter=Q(registrations__status="registered"))
    ).order_by("-active_count")[:6]

    # Category breakdown for visual distribution
    categories = Event.CATEGORY_CHOICES
    category_stats = []
    for code, label in categories:
        count = Event.objects.filter(category=code).count()
        if count > 0:
            category_stats.append({"category": label, "count": count})

    context = {
        "total_events": total_events,
        "total_students": total_students,
        "active_registrations": active_registrations,
        "upcoming_events_count": upcoming_events_count,
        "upcoming_events": upcoming_events,
        "recent_registrations": recent_registrations,
        "category_stats": category_stats,
        "total_capacity": total_capacity,
        "seats_filled_percent": seats_filled_percent,
        "events_by_popularity": events_by_popularity,
    }
    return render(request, "events/admin_dashboard.html", context)


@admin_required
def event_list(request):
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    events = Event.objects.all().order_by("-event_date")

    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(venue__icontains=query) |
            Q(description__icontains=query)
        )
    if category:
        events = events.filter(category=category)

    categories = [c[0] for c in Event.CATEGORY_CHOICES]

    context = {
        "events": events,
        "query": query,
        "selected_category": category,
        "categories": categories,
    }
    return render(request, "events/event_list.html", context)


@admin_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, f"Event '{event.title}' created successfully!")
            return redirect("event_list")
        else:
            messages.error(request, "Please fix the errors in the event form.")
    else:
        form = EventForm(initial={"event_date": timezone.localdate()})

    return render(request, "events/event_form.html", {
        "form": form,
        "is_edit": False,
        "title": "Create New Event"
    })


@admin_required
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Event '{event.title}' updated successfully!")
            return redirect("event_list")
        else:
            messages.error(request, "Please fix the errors in the event form.")
    else:
        form = EventForm(instance=event)

    return render(request, "events/event_form.html", {
        "form": form,
        "is_edit": True,
        "event": event,
        "title": f"Edit Event: {event.title}"
    })


@admin_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        active_count = event.active_registrations_count
        if active_count > 0:
            messages.error(
                request,
                f"Cannot delete '{event.title}' because it has {active_count} active student registration(s). "
                f"Please cancel the registrations first."
            )
            return redirect("event_list")

        title = event.title
        event.delete()
        messages.success(request, f"Event '{title}' has been deleted successfully.")
        return redirect("event_list")

    return redirect("event_list")


@admin_required
def student_list(request):
    query = request.GET.get("q", "").strip()
    dept = request.GET.get("dept", "").strip()
    students = User.objects.filter(role="student").annotate(
        reg_count=Count("registrations", filter=Q(registrations__status="registered"))
    ).order_by("full_name")

    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(username__icontains=query) |
            Q(roll_no__icontains=query) |
            Q(email__icontains=query)
        )
    if dept:
        students = students.filter(department=dept)

    departments = sorted(list(set(User.objects.filter(role="student").values_list("department", flat=True).distinct())))

    context = {
        "students": students,
        "query": query,
        "selected_dept": dept,
        "departments": [d for d in departments if d],
    }
    return render(request, "events/student_list.html", context)


@admin_required
def student_create(request):
    if request.method == "POST":
        form = StudentCreationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                full_name=form.cleaned_data["full_name"],
                roll_no=form.cleaned_data["roll_no"],
                department=form.cleaned_data["department"],
                email=form.cleaned_data["email"],
                role="student"
            )
            messages.success(request, f"Student account for '{user.full_name}' ({user.roll_no}) created successfully!")
            return redirect("student_list")
        else:
            messages.error(request, "Please fix the validation errors below.")
    else:
        form = StudentCreationForm()

    return render(request, "events/student_form.html", {
        "form": form,
        "is_edit": False,
        "title": "Register New Student Account"
    })


@admin_required
def student_update(request, pk):
    student = get_object_or_404(User, pk=pk, role="student")
    if request.method == "POST":
        form = StudentUpdateForm(request.POST, user_instance=student)
        if form.is_valid():
            student.full_name = form.cleaned_data["full_name"]
            student.roll_no = form.cleaned_data["roll_no"]
            student.department = form.cleaned_data["department"]
            student.email = form.cleaned_data["email"]
            new_password = form.cleaned_data["new_password"]
            if new_password:
                student.set_password(new_password)
            student.save()
            messages.success(request, f"Student profile for '{student.full_name}' updated successfully!")
            return redirect("student_list")
        else:
            messages.error(request, "Please fix the validation errors below.")
    else:
        form = StudentUpdateForm(
            initial={
                "full_name": student.full_name,
                "roll_no": student.roll_no,
                "department": student.department,
                "email": student.email,
            },
            user_instance=student
        )

    return render(request, "events/student_form.html", {
        "form": form,
        "is_edit": True,
        "student": student,
        "title": f"Edit Student: {student.full_name}"
    })


@admin_required
def student_delete(request, pk):
    student = get_object_or_404(User, pk=pk, role="student")
    if request.method == "POST":
        name = student.full_name or student.username
        student.delete()
        messages.success(request, f"Student account for '{name}' deleted.")
    return redirect("student_list")


@admin_required
def registration_list(request):
    event_id = request.GET.get("event", "").strip()
    status = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()

    registrations = Registration.objects.select_related("user", "event").order_by("-registration_date")

    if event_id:
        registrations = registrations.filter(event_id=event_id)
    if status in ["registered", "cancelled"]:
        registrations = registrations.filter(status=status)
    if query:
        registrations = registrations.filter(
            Q(user__full_name__icontains=query) |
            Q(user__roll_no__icontains=query) |
            Q(user__username__icontains=query) |
            Q(event__title__icontains=query)
        )

    all_events = Event.objects.all().order_by("title")

    context = {
        "registrations": registrations,
        "all_events": all_events,
        "selected_event": event_id,
        "selected_status": status,
        "query": query,
    }
    return render(request, "events/registration_list.html", context)


# ==============================================================================
# Student Portal Views
# ==============================================================================

@student_required
def student_dashboard(request):
    today = timezone.localdate()
    my_active_regs = Registration.objects.filter(
        user=request.user,
        status="registered"
    ).select_related("event").order_by("event__event_date")

    my_cancelled_count = Registration.objects.filter(
        user=request.user,
        status="cancelled"
    ).count()

    # Nearest upcoming registered event
    next_event_reg = my_active_regs.filter(event__event_date__gte=today).order_by("event__event_date").first()

    # Upcoming available events (max 3)
    registered_event_ids = my_active_regs.values_list("event_id", flat=True)
    available_events = Event.objects.filter(
        event_date__gte=today
    ).exclude(
        id__in=registered_event_ids
    ).order_by("event_date")[:3]

    context = {
        "my_active_regs": my_active_regs,
        "active_count": my_active_regs.count(),
        "cancelled_count": my_cancelled_count,
        "available_events": available_events,
        "next_event_reg": next_event_reg,
    }
    return render(request, "events/student_dashboard.html", context)


@student_required
def browse_events(request):
    today = timezone.localdate()
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "date").strip()

    events_qs = Event.objects.filter(event_date__gte=today)

    if query:
        events_qs = events_qs.filter(
            Q(title__icontains=query) |
            Q(venue__icontains=query) |
            Q(description__icontains=query)
        )
    if category:
        events_qs = events_qs.filter(category=category)

    if sort == "fee":
        events_qs = events_qs.order_by("fee", "event_date")
    elif sort == "seats":
        events_qs = events_qs.order_by("-capacity", "event_date")
    else:
        sort = "date"
        events_qs = events_qs.order_by("event_date")

    # Pre-fetch user's registrations to determine status on each card
    user_regs = {
        r.event_id: r.status
        for r in Registration.objects.filter(user=request.user)
    }

    event_data = []
    for event in events_qs:
        reg_status = user_regs.get(event.id)
        event_data.append({
            "event": event,
            "user_status": reg_status,
            "is_registered": reg_status == "registered",
            "is_cancelled": reg_status == "cancelled",
            "available_seats": event.available_seats,
            "is_full": event.is_full,
        })

    categories = [c[0] for c in Event.CATEGORY_CHOICES]

    context = {
        "event_data": event_data,
        "query": query,
        "selected_category": category,
        "categories": categories,
        "selected_sort": sort,
    }
    return render(request, "events/browse_events.html", context)


@student_required
def my_registrations(request):
    tab = request.GET.get("tab", "active").strip()
    all_regs = Registration.objects.filter(
        user=request.user
    ).select_related("event").order_by("-registration_date")

    active_count = all_regs.filter(status="registered").count()
    cancelled_count = all_regs.filter(status="cancelled").count()
    total_count = all_regs.count()

    if tab == "cancelled":
        registrations = all_regs.filter(status="cancelled")
    elif tab == "all":
        registrations = all_regs
    else:
        tab = "active"
        registrations = all_regs.filter(status="registered")

    context = {
        "registrations": registrations,
        "active_count": active_count,
        "cancelled_count": cancelled_count,
        "total_count": total_count,
        "selected_tab": tab,
    }
    return render(request, "events/my_registrations.html", context)


@login_required
def register_event(request, event_id):
    """Handles event registration or reactivation."""
    if request.method != "POST":
        return redirect("browse_events")

    if not request.user.is_cems_student:
        messages.error(request, "Only students can register for events.")
        return redirect("admin_dashboard")

    with transaction.atomic():
        try:
            event = Event.objects.select_for_update().get(pk=event_id)
        except Event.DoesNotExist:
            messages.error(request, "The specified event could not be found.")
            return redirect("browse_events")

        # 1. Check if past event
        if event.is_past:
            messages.error(request, f"Registration closed: '{event.title}' is already in the past.")
            return redirect("browse_events")

        # 2. Check existing registration
        existing = Registration.objects.filter(user=request.user, event=event).first()
        if existing and existing.status == "registered":
            messages.warning(request, f"You are already registered for '{event.title}'.")
            return redirect("my_registrations")

        # 3. Check capacity limit
        if event.available_seats <= 0:
            messages.error(request, f"Event is full! Capacity limit ({event.capacity} seats) reached.")
            return redirect("browse_events")

        # 4. Reactivate or Create
        if existing:
            existing.status = "registered"
            existing.registration_date = timezone.now()
            existing.save()
            messages.success(request, f"Registration reactivated successfully for '{event.title}'! See you there!")
        else:
            Registration.objects.create(
                user=request.user,
                event=event,
                status="registered"
            )
            messages.success(request, f"Successfully registered for '{event.title}'! Your seat is confirmed.")

    return redirect("my_registrations")


@login_required
def cancel_registration(request, registration_id):
    """Cancels an active registration."""
    if request.method != "POST":
        return redirect("my_registrations")

    reg = get_object_or_404(Registration, pk=registration_id)

    # Permission check: student can only cancel their own, or admin
    if reg.user != request.user and not request.user.is_cems_admin:
        return HttpResponseForbidden("Permission denied: You cannot cancel another student's registration.")

    if reg.status == "cancelled":
        messages.info(request, "This registration is already cancelled.")
    else:
        reg.status = "cancelled"
        reg.save()
        messages.success(request, f"Registration cancelled for {reg.event.title}.")

    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(referer)
    if request.user.is_cems_admin:
        return redirect("registration_list")
    return redirect("my_registrations")
