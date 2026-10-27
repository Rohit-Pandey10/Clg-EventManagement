"""
ui/admin_dashboard.py
Admin Dashboard with dark navy sidebar navigation, live statistic cards,
upcoming events table, and embedded subpages (Events, Students, Registrations).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable

from services.registration_service import get_dashboard_stats
from services.event_service import get_upcoming_events
from ui.event_page import EventPage
from ui.student_page import StudentPage
from ui.registration_page import RegistrationPage


class AdminDashboard(ttk.Frame):
    """
    Main shell for administrator users.
    Features a dark navy sidebar on the left and dynamic content on the right.
    """

    def __init__(self, parent: tk.Widget, admin_user: Dict[str, Any], on_logout: Callable[[], None]):
        super().__init__(parent)
        self.parent = parent
        self.admin_user = admin_user
        self.on_logout = on_logout
        self.active_button: Optional[tk.Button] = None

        self._create_layout()
        self.show_dashboard_overview()

    def _create_layout(self):
        # Configure overall grid
        self.columnconfigure(0, weight=0)  # Sidebar fixed
        self.columnconfigure(1, weight=1)  # Content dynamic
        self.rowconfigure(0, weight=1)

        # 1. Dark Navy Sidebar Frame
        self.sidebar = tk.Frame(self, bg="#0f172a", width=220)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Sidebar Header / Logo
        logo_frame = tk.Frame(self.sidebar, bg="#0f172a")
        logo_frame.pack(fill="x", padx=15, pady=(20, 10))

        tk.Label(
            logo_frame,
            text="🎓 CEMS Admin",
            font=("Segoe UI", 14, "bold"),
            bg="#0f172a",
            fg="#ffffff"
        ).pack(anchor="w")

        tk.Label(
            logo_frame,
            text=f"Logged in as {self.admin_user.get('username')}",
            font=("Segoe UI", 8),
            bg="#0f172a",
            fg="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Divider
        tk.Frame(self.sidebar, bg="#1e293b", height=1).pack(fill="x", padx=15, pady=10)

        # Sidebar Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard", self.show_dashboard_overview),
            ("events", "📅  Manage Events", self.show_events_page),
            ("students", "👥  Manage Students", self.show_students_page),
            ("registrations", "📝  Registrations", self.show_registrations_page),
        ]

        for key, text, cmd in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                command=cmd,
                font=("Segoe UI", 10, "bold"),
                bg="#0f172a",
                fg="#f8fafc",
                activebackground="#1e293b",
                activeforeground="#ffffff",
                bd=0,
                anchor="w",
                padx=15,
                pady=10,
                cursor="hand2"
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.nav_buttons[key] = btn

        # Spacer
        spacer = tk.Frame(self.sidebar, bg="#0f172a")
        spacer.pack(fill="both", expand=True)

        # Logout Button at bottom of sidebar
        logout_btn = tk.Button(
            self.sidebar,
            text="🚪  Logout",
            command=self._handle_logout,
            font=("Segoe UI", 10, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            bd=0,
            anchor="center",
            pady=8,
            cursor="hand2"
        )
        logout_btn.pack(fill="x", padx=15, pady=(0, 20))

        # 2. Main Content Frame
        self.main_container = tk.Frame(self, bg="#f1f5f9")
        self.main_container.grid(row=0, column=1, sticky="nsew")

    def _set_active_button(self, active_key: str):
        """Highlights the active sidebar navigation button."""
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.config(bg="#2563eb", fg="#ffffff")
            else:
                btn.config(bg="#0f172a", fg="#f8fafc")

    def _clear_main_container(self):
        """Clears all children in the main container."""
        for child in self.main_container.winfo_children():
            child.destroy()

    def show_dashboard_overview(self):
        """Renders the primary Dashboard Overview with real-time stats."""
        self._set_active_button("dashboard")
        self._clear_main_container()

        stats = get_dashboard_stats(self.admin_user)

        # Header Card
        header_card = tk.Frame(self.main_container, bg="#ffffff", bd=1, relief="solid")
        header_card.pack(fill="x", padx=20, pady=(20, 15), ipady=10)

        welcome_title = tk.Label(
            header_card,
            text=f"Welcome, {self.admin_user.get('full_name')}!",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        welcome_title.pack(side="left", padx=20)

        refresh_btn = tk.Button(
            header_card,
            text="🔄 Refresh Stats",
            command=self.show_dashboard_overview,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#1e293b",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2"
        )
        refresh_btn.pack(side="right", padx=20)

        # 4 Statistic Cards Grid
        cards_frame = tk.Frame(self.main_container, bg="#f1f5f9")
        cards_frame.pack(fill="x", padx=20, pady=(0, 15))

        cards_data = [
            ("Total Events", str(stats["total_events"]), "#2563eb", "📅"),
            ("Registered Students", str(stats["total_students"]), "#0891b2", "👥"),
            ("Active Registrations", str(stats["active_registrations"]), "#16a34a", "📝"),
            ("Upcoming Events", str(stats["upcoming_events"]), "#d97706", "⏳"),
        ]

        for i, (title_text, value_text, accent_color, icon) in enumerate(cards_data):
            card = tk.Frame(cards_frame, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 10, 0), ipady=12)

            top_row = tk.Frame(card, bg="#ffffff")
            top_row.pack(fill="x", padx=15, pady=(5, 0))

            tk.Label(
                top_row,
                text=icon,
                font=("Segoe UI", 16),
                bg="#ffffff",
                fg=accent_color
            ).pack(side="left")

            tk.Label(
                top_row,
                text=title_text,
                font=("Segoe UI", 9, "bold"),
                bg="#ffffff",
                fg="#64748b"
            ).pack(side="left", padx=8)

            tk.Label(
                card,
                text=value_text,
                font=("Segoe UI", 22, "bold"),
                bg="#ffffff",
                fg=accent_color
            ).pack(anchor="w", padx=15, pady=(5, 5))

        # Upcoming Events Table Section
        events_section = tk.Frame(self.main_container, bg="#ffffff", bd=1, relief="solid")
        events_section.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        section_head = tk.Frame(events_section, bg="#ffffff")
        section_head.pack(fill="x", padx=15, pady=(12, 8))

        tk.Label(
            section_head,
            text="⏳ Upcoming College Events",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        ).pack(side="left")

        # Table of upcoming events
        columns = ("id", "title", "category", "date", "venue", "fee", "capacity", "available")
        tree = ttk.Treeview(
            events_section,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=6
        )

        tree.heading("id", text="ID")
        tree.heading("title", text="Title")
        tree.heading("category", text="Category")
        tree.heading("date", text="Date")
        tree.heading("venue", text="Venue")
        tree.heading("fee", text="Fee")
        tree.heading("capacity", text="Capacity")
        tree.heading("available", text="Available Seats")

        tree.column("id", width=40, anchor="center")
        tree.column("title", width=200, anchor="w")
        tree.column("category", width=90, anchor="center")
        tree.column("date", width=90, anchor="center")
        tree.column("venue", width=140, anchor="w")
        tree.column("fee", width=70, anchor="e")
        tree.column("capacity", width=70, anchor="center")
        tree.column("available", width=90, anchor="center")

        upcoming = get_upcoming_events()
        for ev in upcoming:
            fee_str = "Free" if ev["fee"] == 0 else f"₹{ev['fee']:.2f}"
            tree.insert("", "end", values=(
                ev["event_id"],
                ev["title"],
                ev["category"],
                ev["event_date"],
                ev["venue"],
                fee_str,
                ev["capacity"],
                ev["available_seats"]
            ))

        tree.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def show_events_page(self):
        """Displays the Manage Events page."""
        self._set_active_button("events")
        self._clear_main_container()
        event_page = EventPage(self.main_container, self.admin_user)
        event_page.pack(fill="both", expand=True)

    def show_students_page(self):
        """Displays the Manage Students page."""
        self._set_active_button("students")
        self._clear_main_container()
        student_page = StudentPage(self.main_container, self.admin_user)
        student_page.pack(fill="both", expand=True)

    def show_registrations_page(self):
        """Displays the Registrations page."""
        self._set_active_button("registrations")
        self._clear_main_container()
        reg_page = RegistrationPage(self.main_container, self.admin_user)
        reg_page.pack(fill="both", expand=True)

    def _handle_logout(self):
        confirm = messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?")
        if confirm:
            self.on_logout()
