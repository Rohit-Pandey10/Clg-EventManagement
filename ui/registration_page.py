"""
ui/registration_page.py
Admin screen for viewing all event registrations.
Provides filtering by event, searching by student name, roll number, or event title,
and displays registration status indicators.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, List

from services.registration_service import get_all_registrations
from services.event_service import get_all_events


class RegistrationPage(ttk.Frame):
    """
    View Registrations page for administrators.
    """

    def __init__(self, parent: tk.Widget, admin_user: Dict[str, Any]):
        super().__init__(parent)
        self.parent = parent
        self.admin_user = admin_user
        self.events_map: Dict[str, int] = {}  # Display name -> event_id

        self._create_widgets()
        self._populate_event_filter()
        self.load_registrations()

    def _create_widgets(self):
        # Header
        header_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        header_frame.pack(fill="x", padx=15, pady=(15, 10), ipady=8)

        title = tk.Label(
            header_frame,
            text="📝 Event Registrations",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        title.pack(side="left", padx=15)

        subtitle = tk.Label(
            header_frame,
            text="View and filter all student registrations across events",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#64748b"
        )
        subtitle.pack(side="left", padx=5)

        # Filter Toolbar
        filter_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        filter_card.pack(fill="x", padx=15, pady=(0, 10), ipady=8)

        # Filter by Event
        tk.Label(
            filter_card,
            text="Filter by Event:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b"
        ).pack(side="left", padx=(15, 5))

        self.event_filter_var = tk.StringVar(value="All Events")
        self.combo_events = ttk.Combobox(
            filter_card,
            textvariable=self.event_filter_var,
            state="readonly",
            width=28
        )
        self.combo_events.pack(side="left", padx=5)
        self.combo_events.bind("<<ComboboxSelected>>", lambda e: self.load_registrations())

        # Search Bar
        tk.Label(
            filter_card,
            text="Search (Student / Roll / Event):",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b"
        ).pack(side="left", padx=(15, 5))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            filter_card,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg="#f8fafc",
            bd=1,
            relief="solid",
            width=24
        )
        search_entry.pack(side="left", padx=5, ipady=3)
        search_entry.bind("<Return>", lambda e: self.load_registrations())

        btn_search = tk.Button(
            filter_card,
            text="🔍 Search",
            command=self.load_registrations,
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_search.pack(side="left", padx=10)

        btn_reset = tk.Button(
            filter_card,
            text="Reset",
            command=self._reset_filters,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#1e293b",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_reset.pack(side="left", padx=5)

        # Summary badge bar
        self.summary_label = tk.Label(
            filter_card,
            text="Showing 0 registrations",
            font=("Segoe UI", 9, "italic"),
            bg="#ffffff",
            fg="#64748b"
        )
        self.summary_label.pack(side="right", padx=15)

        # Main Table Card
        table_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        table_card.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        columns = ("reg_id", "student_name", "roll_no", "department", "event_title", "event_date", "reg_date", "status")
        self.tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.tree.heading("reg_id", text="Reg ID")
        self.tree.heading("student_name", text="Student Name")
        self.tree.heading("roll_no", text="Roll Number")
        self.tree.heading("department", text="Department")
        self.tree.heading("event_title", text="Event Title")
        self.tree.heading("event_date", text="Event Date")
        self.tree.heading("reg_date", text="Registration Date")
        self.tree.heading("status", text="Status")

        self.tree.column("reg_id", width=60, anchor="center")
        self.tree.column("student_name", width=160, anchor="w")
        self.tree.column("roll_no", width=110, anchor="center")
        self.tree.column("department", width=120, anchor="w")
        self.tree.column("event_title", width=200, anchor="w")
        self.tree.column("event_date", width=100, anchor="center")
        self.tree.column("reg_date", width=140, anchor="center")
        self.tree.column("status", width=90, anchor="center")

        # Styling tags
        self.tree.tag_configure("registered", foreground="#16a34a", font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("cancelled", foreground="#94a3b8", font=("Segoe UI", 9, "italic"))

        tree_scroll_y = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        tree_scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

    def _populate_event_filter(self):
        """Populates the event dropdown with all existing events."""
        events = get_all_events()
        self.events_map = {"All Events": 0}
        options = ["All Events"]

        for ev in events:
            label = f"#{ev['event_id']} - {ev['title']} ({ev['event_date']})"
            self.events_map[label] = ev["event_id"]
            options.append(label)

        current = self.event_filter_var.get()
        self.combo_events["values"] = options
        if current in self.events_map:
            self.combo_events.set(current)
        else:
            self.combo_events.set("All Events")

    def load_registrations(self, refresh_events: bool = True):
        """Fetches and displays registrations according to current filters."""
        if refresh_events:
            self._populate_event_filter()

        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_event_label = self.event_filter_var.get()
        event_id_filter = self.events_map.get(selected_event_label, 0)
        search_term = self.search_var.get()

        registrations = get_all_registrations(
            search_query=search_term,
            event_id_filter=event_id_filter if event_id_filter > 0 else None,
            admin_user=self.admin_user
        )

        active_count = 0
        cancelled_count = 0

        for r in registrations:
            status = r["status"]
            if status == "registered":
                active_count += 1
                status_text = "Registered"
            else:
                cancelled_count += 1
                status_text = "Cancelled"

            self.tree.insert(
                "",
                "end",
                values=(
                    r["registration_id"],
                    r["student_name"],
                    r["roll_no"] or "N/A",
                    r["department"] or "General",
                    r["event_title"],
                    r["event_date"],
                    r["registration_date"],
                    status_text
                ),
                tags=(status,)
            )

        total = len(registrations)
        self.summary_label.config(
            text=f"Total: {total} | Active: {active_count} | Cancelled: {cancelled_count}"
        )

    def _reset_filters(self):
        """Resets filters to default and reloads."""
        self.search_var.set("")
        self.event_filter_var.set("All Events")
        self._populate_event_filter()
        self.load_registrations()
