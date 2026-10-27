"""
ui/event_page.py
Admin screen for managing college events.
Provides event CRUD operations, ttk.Treeview table, search, category filters,
and form population on row selection.
"""

from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

from services.event_service import (
    get_all_events,
    create_event,
    update_event,
    delete_event,
    CATEGORIES
)


class EventPage(ttk.Frame):
    """
    Manage Events page for administrators.
    """

    def __init__(self, parent: tk.Widget, admin_user: Dict[str, Any]):
        super().__init__(parent)
        self.parent = parent
        self.admin_user = admin_user
        self.selected_event_id: Optional[int] = None

        self._create_widgets()
        self.load_events()

    def _create_widgets(self):
        # Top Header
        header_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        header_frame.pack(fill="x", padx=15, pady=(15, 10), ipady=8)

        title = tk.Label(
            header_frame,
            text="📅 Manage Events",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        title.pack(side="left", padx=15)

        subtitle = tk.Label(
            header_frame,
            text="Create, modify, search, and delete college events",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#64748b"
        )
        subtitle.pack(side="left", padx=5)

        # Search and Filter Toolbar
        search_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        search_card.pack(fill="x", padx=15, pady=(0, 10), ipady=6)

        tk.Label(
            search_card,
            text="Search:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b"
        ).pack(side="left", padx=(15, 5))

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_card,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg="#f8fafc",
            bd=1,
            relief="solid",
            width=25
        )
        search_entry.pack(side="left", padx=5, ipady=3)
        search_entry.bind("<Return>", lambda e: self.load_events())

        tk.Label(
            search_card,
            text="Category:",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b"
        ).pack(side="left", padx=(15, 5))

        self.category_filter_var = tk.StringVar(value="All")
        cat_options = ["All"] + CATEGORIES
        cat_dropdown = ttk.Combobox(
            search_card,
            textvariable=self.category_filter_var,
            values=cat_options,
            state="readonly",
            width=14
        )
        cat_dropdown.pack(side="left", padx=5)
        cat_dropdown.bind("<<ComboboxSelected>>", lambda e: self.load_events())

        btn_search = tk.Button(
            search_card,
            text="🔍 Search",
            command=self.load_events,
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
            search_card,
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

        # Main Split Content: Top is Treeview Table, Bottom is Form
        content_frame = tk.Frame(self, bg="#f1f5f9")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 1. Treeview Frame
        table_frame = tk.Frame(content_frame, bg="#ffffff", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("id", "title", "category", "date", "venue", "fee", "capacity", "registered", "available")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Event Title")
        self.tree.heading("category", text="Category")
        self.tree.heading("date", text="Date")
        self.tree.heading("venue", text="Venue")
        self.tree.heading("fee", text="Fee (₹)")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("registered", text="Registered")
        self.tree.heading("available", text="Available")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("category", width=100, anchor="center")
        self.tree.column("date", width=95, anchor="center")
        self.tree.column("venue", width=140, anchor="w")
        self.tree.column("fee", width=70, anchor="e")
        self.tree.column("capacity", width=70, anchor="center")
        self.tree.column("registered", width=80, anchor="center")
        self.tree.column("available", width=75, anchor="center")

        tree_scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        tree_scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 2. Form Card
        form_card = tk.Frame(content_frame, bg="#ffffff", bd=1, relief="solid")
        form_card.pack(fill="x", pady=(0, 0), ipadx=10, ipady=10)

        form_title = tk.Label(
            form_card,
            text="Event Details Form",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        form_title.grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(0, 8))

        # Grid row 1: Title, Category, Date
        tk.Label(form_card, text="Event Title *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=1, column=0, sticky="w", padx=10, pady=2)
        self.title_var = tk.StringVar()
        self.entry_title = tk.Entry(form_card, textvariable=self.title_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=26)
        self.entry_title.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 6), ipady=3)

        tk.Label(form_card, text="Category *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=1, column=1, sticky="w", padx=10, pady=2)
        self.form_category_var = tk.StringVar(value=CATEGORIES[0])
        self.combo_category = ttk.Combobox(form_card, textvariable=self.form_category_var, values=CATEGORIES, state="readonly", width=18)
        self.combo_category.grid(row=2, column=1, sticky="w", padx=10, pady=(0, 6))

        tk.Label(form_card, text="Date (YYYY-MM-DD) *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=1, column=2, sticky="w", padx=10, pady=2)
        date_frame = tk.Frame(form_card, bg="#ffffff")
        date_frame.grid(row=2, column=2, sticky="w", padx=10, pady=(0, 6))

        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.entry_date = tk.Entry(date_frame, textvariable=self.date_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=14)
        self.entry_date.pack(side="left", ipady=3)

        btn_today = tk.Button(date_frame, text="Today", command=lambda: self.date_var.set(date.today().isoformat()), font=("Segoe UI", 8), bg="#e2e8f0", bd=0, padx=4, cursor="hand2")
        btn_today.pack(side="left", padx=4)

        # Grid row 2: Venue, Fee, Capacity
        tk.Label(form_card, text="Venue *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=3, column=0, sticky="w", padx=10, pady=2)
        self.venue_var = tk.StringVar()
        self.entry_venue = tk.Entry(form_card, textvariable=self.venue_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=26)
        self.entry_venue.grid(row=4, column=0, sticky="w", padx=10, pady=(0, 6), ipady=3)

        tk.Label(form_card, text="Registration Fee (₹) *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=3, column=1, sticky="w", padx=10, pady=2)
        self.fee_var = tk.StringVar(value="0")
        self.entry_fee = tk.Entry(form_card, textvariable=self.fee_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=20)
        self.entry_fee.grid(row=4, column=1, sticky="w", padx=10, pady=(0, 6), ipady=3)

        tk.Label(form_card, text="Capacity (Seats) *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=3, column=2, sticky="w", padx=10, pady=2)
        self.capacity_var = tk.StringVar(value="50")
        self.entry_capacity = tk.Entry(form_card, textvariable=self.capacity_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=20)
        self.entry_capacity.grid(row=4, column=2, sticky="w", padx=10, pady=(0, 6), ipady=3)

        # Grid row 3: Description
        tk.Label(form_card, text="Description", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=5, column=0, sticky="w", padx=10, pady=2)
        self.desc_var = tk.StringVar()
        self.entry_desc = tk.Entry(form_card, textvariable=self.desc_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=70)
        self.entry_desc.grid(row=6, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10), ipady=3)

        # Form Buttons
        btn_frame = tk.Frame(form_card, bg="#ffffff")
        btn_frame.grid(row=7, column=0, columnspan=6, sticky="w", padx=10, pady=(5, 0))

        self.btn_add = tk.Button(
            btn_frame,
            text="➕ Add Event",
            command=self._handle_add,
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2"
        )
        self.btn_add.pack(side="left", padx=(0, 8))

        self.btn_update = tk.Button(
            btn_frame,
            text="💾 Update Event",
            command=self._handle_update,
            font=("Segoe UI", 9, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled"
        )
        self.btn_update.pack(side="left", padx=8)

        self.btn_delete = tk.Button(
            btn_frame,
            text="🗑️ Delete Event",
            command=self._handle_delete,
            font=("Segoe UI", 9, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            state="disabled"
        )
        self.btn_delete.pack(side="left", padx=8)

        self.btn_clear = tk.Button(
            btn_frame,
            text="🧹 Clear Form",
            command=self._clear_form,
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg="#334155",
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2"
        )
        self.btn_clear.pack(side="left", padx=8)

    def load_events(self):
        """Fetches events from database and updates treeview."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_var.get()
        cat = self.category_filter_var.get()
        events = get_all_events(search_query=search, category_filter=cat)

        for ev in events:
            fee_display = f"Free" if ev["fee"] == 0 else f"{ev['fee']:.2f}"
            self.tree.insert("", "end", values=(
                ev["event_id"],
                ev["title"],
                ev["category"],
                ev["event_date"],
                ev["venue"],
                fee_display,
                ev["capacity"],
                ev["registered_count"],
                ev["available_seats"]
            ))

    def _on_tree_select(self, event):
        """Populates form when a row in Treeview is selected."""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        values = self.tree.item(item, "values")
        if not values:
            return

        self.selected_event_id = int(values[0])

        # Fetch detailed info including description
        from services.event_service import get_event_by_id
        ev = get_event_by_id(self.selected_event_id)
        if not ev:
            return

        self.title_var.set(ev["title"])
        self.form_category_var.set(ev["category"])
        self.date_var.set(ev["event_date"])
        self.venue_var.set(ev["venue"])
        self.fee_var.set(str(ev["fee"]))
        self.capacity_var.set(str(ev["capacity"]))
        self.desc_var.set(ev["description"] or "")

        # Enable Update and Delete buttons, disable Add
        self.btn_add.config(state="disabled")
        self.btn_update.config(state="normal")
        self.btn_delete.config(state="normal")

    def _handle_add(self):
        """Handles adding a new event."""
        success, msg = create_event(
            title=self.title_var.get(),
            category=self.form_category_var.get(),
            event_date_str=self.date_var.get(),
            venue=self.venue_var.get(),
            description=self.desc_var.get(),
            fee_str=self.fee_var.get(),
            capacity_str=self.capacity_var.get(),
            admin_user=self.admin_user
        )

        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_events()
        else:
            messagebox.showerror("Error", msg)

    def _handle_update(self):
        """Handles updating an existing event."""
        if not self.selected_event_id:
            messagebox.showwarning("Warning", "Please select an event to update.")
            return

        success, msg = update_event(
            event_id=self.selected_event_id,
            title=self.title_var.get(),
            category=self.form_category_var.get(),
            event_date_str=self.date_var.get(),
            venue=self.venue_var.get(),
            description=self.desc_var.get(),
            fee_str=self.fee_var.get(),
            capacity_str=self.capacity_var.get(),
            admin_user=self.admin_user
        )

        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_events()
        else:
            messagebox.showerror("Error", msg)

    def _handle_delete(self):
        """Handles deleting an event with confirmation dialog."""
        if not self.selected_event_id:
            messagebox.showwarning("Warning", "Please select an event to delete.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete event ID {self.selected_event_id} ({self.title_var.get()})?\nThis action cannot be undone."
        )
        if not confirm:
            return

        success, msg = delete_event(self.selected_event_id, self.admin_user)
        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_events()
        else:
            messagebox.showerror("Cannot Delete", msg)

    def _clear_form(self):
        """Resets form inputs and button states."""
        self.selected_event_id = None
        self.title_var.set("")
        self.form_category_var.set(CATEGORIES[0])
        self.date_var.set(date.today().isoformat())
        self.venue_var.set("")
        self.fee_var.set("0")
        self.capacity_var.set("50")
        self.desc_var.set("")

        # Reset button states
        self.btn_add.config(state="normal")
        self.btn_update.config(state="disabled")
        self.btn_delete.config(state="disabled")

        # Deselect in Treeview
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def _reset_filters(self):
        """Resets search filters and reloads table."""
        self.search_var.set("")
        self.category_filter_var.set("All")
        self.load_events()
