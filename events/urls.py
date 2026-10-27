from django.urls import path
from . import views

urlpatterns = [
    # Root & Auth
    path("", views.dashboard_view, name="index"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_student_view, name="register"),

    # Admin Portal
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/events/", views.event_list, name="event_list"),
    path("admin/events/new/", views.event_create, name="event_create"),
    path("admin/events/<int:pk>/edit/", views.event_update, name="event_update"),
    path("admin/events/<int:pk>/delete/", views.event_delete, name="event_delete"),
    path("admin/students/", views.student_list, name="student_list"),
    path("admin/students/new/", views.student_create, name="student_create"),
    path("admin/students/<int:pk>/edit/", views.student_update, name="student_update"),
    path("admin/students/<int:pk>/delete/", views.student_delete, name="student_delete"),
    path("admin/registrations/", views.registration_list, name="registration_list"),

    # Student Portal
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/browse/", views.browse_events, name="browse_events"),
    path("student/my-registrations/", views.my_registrations, name="my_registrations"),
    path("student/register/<int:event_id>/", views.register_event, name="register_event"),
    path("student/cancel/<int:registration_id>/", views.cancel_registration, name="cancel_registration"),
]

