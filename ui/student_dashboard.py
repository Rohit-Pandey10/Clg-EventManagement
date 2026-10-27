"""
ui/student_dashboard.py
Student Dashboard for viewing upcoming events, viewing event details,
registering for events, viewing own registrations, and cancelling registrations.
"""

from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional

from services.event_service import get_upcoming_events, get_event_by_id, CATEGORIES
from services.registration_service import (
    register_for_event,
    cancel_registration,
    get_student_registrations
)


class StudentDashboard(ttk.Frame):
    """
    Main portal interface for Student users.
    """

    def __init__(self, parent: tk.Widget, student_user: Dict[str, Any], on_logout: Callable[[], None]):
        super().__init__(parent)
        self.parent = parent
        self.student_user = student_user
        self.on_logout = on_logout
        self.selected_upcoming_event_id: Optional[int] = None
        self.selected_my_reg_id: Optional[int] = None

        self._create_widgets()
        self.load_upcoming_events()
        self.load_my_registrations()

    def _create_widgets(self):
        # Top Header Bar
        header_bar = tk.Frame(self, bg="#0f172a", height=60)
        header_bar.pack(fill="x")

        # Title & Welcome info
        title_box = tk.Frame(header_bar, bg="#0f172a")
        title_box.pack(side="left", padx=20, pady=10)

        tk.Label(
            title_box,
            text="🎓 College Event Management - Student Portal",
            font=("Segoe UI", 14, "bold"),
            bg="#0f172a",
            fg="#ffffff"
        ).pack(anchor="w")

        roll = self.student_user.get("roll_no") or "N/A"
        dept = self.student_user.get("department") or "Student"
        tk.Label(
            title_box,
            text=f"Welcome, {self.student_user.get('full_name')}  |  Roll No: {roll}  |  Dept: {dept}",
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg="#94a3b8"
        ).pack(anchor="w")

        # Logout Button
        logout_btn = tk.Button(
            header_bar,
            text="🚪 Logout",
            command=self._handle_logout,
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2"
        )
        logout_btn.pack(side="right", padx=20, pady=12)

        # Tabbed Notebook Container
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=15)

        # Tab 1: Upcoming Events
        self.tab_events = tk.Frame(self.notebook, bg="#f1f5f9")
        self.notebook.add(self.tab_events, text="  📅 Upcoming Events  ")
        self._build_events_tab()

        # Tab 2: My Registrations
        self.tab_my_reg = tk.Frame(self.notebook, bg="#f1f5f9")
        self.notebook.add(self.tab_my_reg, text="  🎫 My Registrations  ")
        self._build_my_registrations_tab()

    def _build_events_tab(self):
        # Search & Filter bar
        filter_card = tk.Frame(self.tab_events, bg="#ffffff", bd=1, relief="solid")
        filter_card.pack(fill="x", pady=(10, 10), ipady=6)

        tk.Label(
            filter_card,
            text="Search Events:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b"
        ).pack(side="left", padx=(15, 5))

        self.search_event_var = tk.StringVar()
        entry_search = tk.Entry(
            filter_card,
            textvariable=self.search_event_var,
            font=("Segoe UI", 10),
            bg="#f8fafc",
            bd=1,
            relief="solid",
            width=24
        )
        entry_search.pack(side="left", padx=5, ipady=3)
        entry_search.bind("<Return>", lambda e: self.load_upcoming_events())

        tk.Label(
            filter_card,
            text="Category:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b"
        ).pack(side="left", padx=(15, 5))

        self.cat_filter_var = tk.StringVar(value="All")
        cat_combobox = ttk.Combobox(
            filter_card,
            textvariable=self.cat_filter_var,
            values=["All"] + CATEGORIES,
            state="readonly",
            width=14
        )
        cat_combobox.pack(side="left", padx=5)
        cat_combobox.bind("<<ComboboxSelected>>", lambda e: self.load_upcoming_events())

        btn_search = tk.Button(
            filter_card,
            text="🔍 Search",
            command=self.load_upcoming_events,
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
            command=self._reset_event_search,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#1e293b",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_reset.pack(side="left", padx=5)

        # Split: Table on Top, Details Card on Bottom
        split_frame = tk.Frame(self.tab_events, bg="#f1f5f9")
        split_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Table Frame
        table_card = tk.Frame(split_frame, bg="#ffffff", bd=1, relief="solid")
        table_card.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("id", "title", "category", "date", "venue", "fee", "available")
        self.events_tree = ttk.Treeview(
            table_card,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=7
        )

        self.events_tree.heading("id", text="ID")
        self.events_tree.heading("title", text="Event Title")
        self.events_tree.heading("category", text="Category")
        self.events_tree.heading("date", text="Date")
        self.events_tree.heading("venue", text="Venue")
        self.events_tree.heading("fee", text="Fee")
        self.events_tree.heading("available", text="Available Seats")

        self.events_tree.column("id", width=45, anchor="center")
        self.events_tree.column("title", width=240, anchor="w")
        self.events_tree.column("category", width=100, anchor="center")
        self.events_tree.column("date", width=95, anchor="center")
        self.events_tree.column("venue", width=160, anchor="w")
        self.events_tree.column("fee", width=80, anchor="e")
        self.events_tree.column("available", width=100, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_card, orient="vertical", command=self.events_tree.yview)
        self.events_tree.configure(yscrollcommand=tree_scroll_y.set)

        self.events_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        tree_scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.events_tree.bind("<<TreeviewSelect>>", self._on_event_select)

        # Selected Event Details Card
        self.details_card = tk.Frame(split_frame, bg="#ffffff", bd=1, relief="solid")
        self.details_card.pack(fill="x", ipady=10)

        details_header = tk.Frame(self.details_card, bg="#ffffff")
        details_header.pack(fill="x", padx=15, pady=(5, 5))

        self.lbl_selected_title = tk.Label(
            details_header,
            text="Select an event from the table above to view details",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        self.lbl_selected_title.pack(side="left")

        # Action button on right
        self.btn_register = tk.Button(
            details_header,
            text="📝 Register for Event",
            command=self._handle_register,
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            state="disabled"
        )
        self.btn_register.pack(side="right")

        # Detail Labels Container
        self.info_grid = tk.Frame(self.details_card, bg="#ffffff")
        self.info_grid.pack(fill="x", padx=15, pady=(5, 5))

        self.lbl_detail_cat = tk.Label(self.info_grid, text="Category: -", font=("Segoe UI", 9), bg="#ffffff", fg="#475569")
        self.lbl_detail_cat.grid(row=0, column=0, sticky="w", padx=(0, 20), pady=2)

        self.lbl_detail_date = tk.Label(self.info_grid, text="Date: -", font=("Segoe UI", 9), bg="#ffffff", fg="#475569")
        self.lbl_detail_date.grid(row=0, column=1, sticky="w", padx=(0, 20), pady=2)

        self.lbl_detail_venue = tk.Label(self.info_grid, text="Venue: -", font=("Segoe UI", 9), bg="#ffffff", fg="#475569")
        self.lbl_detail_venue.grid(row=0, column=2, sticky="w", padx=(0, 20), pady=2)

        self.lbl_detail_fee = tk.Label(self.info_grid, text="Fee: -", font=("Segoe UI", 9), bg="#ffffff", fg="#475569")
        self.lbl_detail_fee.grid(row=0, column=3, sticky="w", padx=(0, 20), pady=2)

        self.lbl_detail_seats = tk.Label(self.info_grid, text="Available Seats: -", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#16a34a")
        self.lbl_detail_seats.grid(row=0, column=4, sticky="w", pady=2)

        self.lbl_detail_desc = tk.Label(
            self.details_card,
            text="Description: Please choose an event from the list.",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#334155",
            wraplength=800,
            justify="left"
        )
        self.lbl_detail_desc.pack(anchor="w", padx=15, pady=(5, 5))

    def _build_my_registrations_tab(self):
        # Header toolbar
        tool_card = tk.Frame(self.tab_my_reg, bg="#ffffff", bd=1, relief="solid")
        tool_card.pack(fill="x", pady=(10, 10), ipady=6)

        tk.Label(
            tool_card,
            text="My Event Registrations",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        ).pack(side="left", padx=15)

        self.lbl_reg_count = tk.Label(
            tool_card,
            text="Total registrations: 0",
            font=("Segoe UI", 9, "italic"),
            bg="#ffffff",
            fg="#64748b"
        )
        self.lbl_reg_count.pack(side="left", padx=10)

        btn_refresh = tk.Button(
            tool_card,
            text="🔄 Refresh",
            command=self.load_my_registrations,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#1e293b",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        btn_refresh.pack(side="right", padx=15)

        # Registrations Table
        reg_table_card = tk.Frame(self.tab_my_reg, bg="#ffffff", bd=1, relief="solid")
        reg_table_card.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("reg_id", "title", "category", "event_date", "venue", "fee", "reg_date", "status")
        self.my_reg_tree = ttk.Treeview(
            reg_table_card,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.my_reg_tree.heading("reg_id", text="Reg ID")
        self.my_reg_tree.heading("title", text="Event Title")
        self.my_reg_tree.heading("category", text="Category")
        self.my_reg_tree.heading("event_date", text="Event Date")
        self.my_reg_tree.heading("venue", text="Venue")
        self.my_reg_tree.heading("fee", text="Fee")
        self.my_reg_tree.heading("reg_date", text="Registration Date")
        self.my_reg_tree.heading("status", text="Status")

        self.my_reg_tree.column("reg_id", width=60, anchor="center")
        self.my_reg_tree.column("title", width=220, anchor="w")
        self.my_reg_tree.column("category", width=100, anchor="center")
        self.my_reg_tree.column("event_date", width=95, anchor="center")
        self.my_reg_tree.column("venue", width=140, anchor="w")
        self.my_reg_tree.column("fee", width=70, anchor="e")
        self.my_reg_tree.column("reg_date", width=140, anchor="center")
        self.my_reg_tree.column("status", width=90, anchor="center")

        self.my_reg_tree.tag_configure("registered", foreground="#16a34a", font=("Segoe UI", 9, "bold"))
        self.my_reg_tree.tag_configure("cancelled", foreground="#94a3b8", font=("Segoe UI", 9, "italic"))

        reg_scroll_y = ttk.Scrollbar(reg_table_card, orient="vertical", command=self.my_reg_tree.yview)
        self.my_reg_tree.configure(yscrollcommand=reg_scroll_y.set)

        self.my_reg_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        reg_scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.my_reg_tree.bind("<<TreeviewSelect>>", self._on_my_reg_select)

        # Bottom Action Bar
        bottom_bar = tk.Frame(self.tab_my_reg, bg="#ffffff", bd=1, relief="solid")
        bottom_bar.pack(fill="x", pady=(0, 10), ipady=8)

        tk.Label(
            bottom_bar,
            text="Tip: Active registrations can be cancelled. Cancelled registrations can be reactivated before the event date if seats remain.",
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#64748b"
        ).pack(side="left", padx=15)

        self.btn_cancel_reg = tk.Button(
            bottom_bar,
            text="❌ Cancel Selected Registration",
            command=self._handle_cancel_registration,
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            bd=0,
            padx=14,
            pady=5,
            cursor="hand2",
            state="disabled"
        )
        self.btn_cancel_reg.pack(side="right", padx=15)

    def load_upcoming_events(self):
        """Loads future events into Treeview."""
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)

        search = self.search_event_var.get()
        cat = self.cat_filter_var.get()
        events = get_upcoming_events(search_query=search, category_filter=cat)

        for ev in events:
            fee_display = "Free" if ev["fee"] == 0 else f"₹{ev['fee']:.2f}"
            self.events_tree.insert("", "end", values=(
                ev["event_id"],
                ev["title"],
                ev["category"],
                ev["event_date"],
                ev["venue"],
                fee_display,
                ev["available_seats"]
            ))

        self._clear_event_details()

    def _on_event_select(self, event):
        """Displays details for selected event and enables register button."""
        selected = self.events_tree.selection()
        if not selected:
            return

        values = self.events_tree.item(selected[0], "values")
        if not values:
            return

        self.selected_upcoming_event_id = int(values[0])
        ev = get_event_by_id(self.selected_upcoming_event_id)
        if not ev:
            return

        self.lbl_selected_title.config(text=f"Selected: {ev['title']}")
        self.lbl_detail_cat.config(text=f"Category: {ev['category']}")
        self.lbl_detail_date.config(text=f"Date: {ev['event_date']}")
        self.lbl_detail_venue.config(text=f"Venue: {ev['venue']}")
        fee_str = "Free" if ev["fee"] == 0 else f"₹{ev['fee']:.2f}"
        self.lbl_detail_fee.config(text=f"Fee: {fee_str}")

        avail = ev["available_seats"]
        if avail > 0:
            self.lbl_detail_seats.config(text=f"Available Seats: {avail} / {ev['capacity']}", fg="#16a34a")
            self.btn_register.config(state="normal", text="📝 Register for Event", bg="#2563eb")
        else:
            self.lbl_detail_seats.config(text=f"Available Seats: FULL (0 / {ev['capacity']})", fg="#dc2626")
            self.btn_register.config(state="disabled", text="Event Full", bg="#94a3b8")

        desc = ev["description"] if ev["description"] else "No description provided."
        self.lbl_detail_desc.config(text=f"Description: {desc}")

    def _clear_event_details(self):
        self.selected_upcoming_event_id = None
        self.lbl_selected_title.config(text="Select an event from the table above to view details")
        self.lbl_detail_cat.config(text="Category: -")
        self.lbl_detail_date.config(text="Date: -")
        self.lbl_detail_venue.config(text="Venue: -")
        self.lbl_detail_fee.config(text="Fee: -")
        self.lbl_detail_seats.config(text="Available Seats: -", fg="#16a34a")
        self.lbl_detail_desc.config(text="Description: Please choose an event from the list.")
        self.btn_register.config(state="disabled", text="📝 Register for Event", bg="#2563eb")

    def _handle_register(self):
        """Registers the logged in student for the selected event."""
        if not self.selected_upcoming_event_id:
            messagebox.showwarning("Warning", "Please select an event to register.")
            return

        confirm = messagebox.askyesno(
            "Confirm Registration",
            f"Do you want to confirm your registration for this event?"
        )
        if not confirm:
            return

        success, msg = register_for_event(
            user_id=self.student_user["user_id"],
            event_id=self.selected_upcoming_event_id,
            current_user=self.student_user
        )

        if success:
            messagebox.showinfo("Registration Successful", msg)
            self.load_upcoming_events()
            self.load_my_registrations()
            # Switch to My Registrations tab so student immediately sees their confirmation
            self.notebook.select(self.tab_my_reg)
        else:
            messagebox.showerror("Registration Failed", msg)

    def load_my_registrations(self):
        """Loads logged in student's registration history."""
        for item in self.my_reg_tree.get_children():
            self.my_reg_tree.delete(item)

        regs = get_student_registrations(
            user_id=self.student_user["user_id"],
            current_user=self.student_user
        )

        active = 0
        for r in regs:
            status = r["status"]
            if status == "registered":
                active += 1
                status_display = "Registered"
            else:
                status_display = "Cancelled"

            fee_str = "Free" if r["fee"] == 0 else f"₹{r['fee']:.2f}"
            self.my_reg_tree.insert(
                "",
                "end",
                values=(
                    r["registration_id"],
                    r["event_title"],
                    r["category"],
                    r["event_date"],
                    r["venue"],
                    fee_str,
                    r["registration_date"],
                    status_display
                ),
                tags=(status,)
            )

        self.lbl_reg_count.config(text=f"Total: {len(regs)} (Active: {active})")
        self.btn_cancel_reg.config(state="disabled")

    def _on_my_reg_select(self, event):
        """Enables cancel button if selected registration is active."""
        selected = self.my_reg_tree.selection()
        if not selected:
            return

        values = self.my_reg_tree.item(selected[0], "values")
        if not values:
            return

        self.selected_my_reg_id = int(values[0])
        status = values[7]

        if status == "Registered":
            self.btn_cancel_reg.config(state="normal")
        else:
            self.btn_cancel_reg.config(state="disabled")

    def _handle_cancel_registration(self):
        """Cancels selected registration."""
        if not self.selected_my_reg_id:
            messagebox.showwarning("Warning", "Please select a registration to cancel.")
            return

        confirm = messagebox.askyesno(
            "Confirm Cancellation",
            "Are you sure you want to cancel your registration for this event?"
        )
        if not confirm:
            return

        success, msg = cancel_registration(self.selected_my_reg_id, self.student_user)
        if success:
            messagebox.showinfo("Cancellation Confirmed", msg)
            self.load_my_registrations()
            self.load_upcoming_events()
        else:
            messagebox.showerror("Error", msg)

    def _reset_event_search(self):
        self.search_event_var.set("")
        self.cat_filter_var.set("All")
        self.load_upcoming_events()

    def _handle_logout(self):
        confirm = messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?")
        if confirm:
            self.on_logout()
