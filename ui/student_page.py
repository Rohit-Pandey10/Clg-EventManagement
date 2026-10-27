"""
ui/student_page.py
Admin screen for managing student accounts.
Provides student creation, profile updating, search, and validation.
Passwords are never displayed in the table.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

from services.student_service import (
    get_all_students,
    create_student,
    update_student,
    get_student_by_id
)


class StudentPage(ttk.Frame):
    """
    Manage Students page for administrators.
    """

    def __init__(self, parent: tk.Widget, admin_user: Dict[str, Any]):
        super().__init__(parent)
        self.parent = parent
        self.admin_user = admin_user
        self.selected_user_id: Optional[int] = None

        self._create_widgets()
        self.load_students()

    def _create_widgets(self):
        # Top Header
        header_frame = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        header_frame.pack(fill="x", padx=15, pady=(15, 10), ipady=8)

        title = tk.Label(
            header_frame,
            text="👥 Manage Students",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        title.pack(side="left", padx=15)

        subtitle = tk.Label(
            header_frame,
            text="Register new students, update records, and search student database",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#64748b"
        )
        subtitle.pack(side="left", padx=5)

        # Search Toolbar
        search_card = tk.Frame(self, bg="#ffffff", bd=1, relief="solid")
        search_card.pack(fill="x", padx=15, pady=(0, 10), ipady=6)

        tk.Label(
            search_card,
            text="Search Students (Name / Roll No / Dept):",
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
            width=30
        )
        search_entry.pack(side="left", padx=5, ipady=3)
        search_entry.bind("<Return>", lambda e: self.load_students())

        btn_search = tk.Button(
            search_card,
            text="🔍 Search",
            command=self.load_students,
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

        # Split Layout: Table on Top, Form on Bottom
        content_frame = tk.Frame(self, bg="#f1f5f9")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 1. Treeview Frame
        table_frame = tk.Frame(content_frame, bg="#ffffff", bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("id", "roll_no", "full_name", "username", "department", "email")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("roll_no", text="Roll Number")
        self.tree.heading("full_name", text="Full Name")
        self.tree.heading("username", text="Username")
        self.tree.heading("department", text="Department")
        self.tree.heading("email", text="Email Address")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("roll_no", width=120, anchor="center")
        self.tree.column("full_name", width=180, anchor="w")
        self.tree.column("username", width=130, anchor="w")
        self.tree.column("department", width=140, anchor="w")
        self.tree.column("email", width=200, anchor="w")

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
            text="Student Details Form",
            font=("Segoe UI", 11, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        form_title.grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(0, 8))

        # Row 1: Full Name, Roll No, Department
        tk.Label(form_card, text="Full Name *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=1, column=0, sticky="w", padx=10, pady=2)
        self.name_var = tk.StringVar()
        self.entry_name = tk.Entry(form_card, textvariable=self.name_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=25)
        self.entry_name.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 6), ipady=3)

        tk.Label(form_card, text="Roll Number *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=1, column=1, sticky="w", padx=10, pady=2)
        self.roll_var = tk.StringVar()
        self.entry_roll = tk.Entry(form_card, textvariable=self.roll_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=20)
        self.entry_roll.grid(row=2, column=1, sticky="w", padx=10, pady=(0, 6), ipady=3)

        tk.Label(form_card, text="Department *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=1, column=2, sticky="w", padx=10, pady=2)
        self.dept_var = tk.StringVar()
        self.entry_dept = tk.Entry(form_card, textvariable=self.dept_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=25)
        self.entry_dept.grid(row=2, column=2, sticky="w", padx=10, pady=(0, 6), ipady=3)

        # Row 2: Username, Password, Email
        tk.Label(form_card, text="Username *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=3, column=0, sticky="w", padx=10, pady=2)
        self.username_var = tk.StringVar()
        self.entry_username = tk.Entry(form_card, textvariable=self.username_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=25)
        self.entry_username.grid(row=4, column=0, sticky="w", padx=10, pady=(0, 6), ipady=3)

        self.pass_label = tk.Label(form_card, text="Password *", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155")
        self.pass_label.grid(row=3, column=1, sticky="w", padx=10, pady=2)
        self.password_var = tk.StringVar()
        self.entry_password = tk.Entry(form_card, textvariable=self.password_var, show="•", font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=20)
        self.entry_password.grid(row=4, column=1, sticky="w", padx=10, pady=(0, 6), ipady=3)

        tk.Label(form_card, text="Email Address", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").grid(row=3, column=2, sticky="w", padx=10, pady=2)
        self.email_var = tk.StringVar()
        self.entry_email = tk.Entry(form_card, textvariable=self.email_var, font=("Segoe UI", 9), bg="#f8fafc", bd=1, relief="solid", width=25)
        self.entry_email.grid(row=4, column=2, sticky="w", padx=10, pady=(0, 6), ipady=3)

        # Buttons
        btn_frame = tk.Frame(form_card, bg="#ffffff")
        btn_frame.grid(row=5, column=0, columnspan=6, sticky="w", padx=10, pady=(8, 0))

        self.btn_add = tk.Button(
            btn_frame,
            text="➕ Add Student",
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
            text="💾 Update Student",
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

    def load_students(self):
        """Loads students from database into Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_var.get()
        students = get_all_students(search_query=search)

        for s in students:
            self.tree.insert("", "end", values=(
                s["user_id"],
                s["roll_no"] or "N/A",
                s["full_name"],
                s["username"],
                s["department"] or "General",
                s["email"] or "N/A"
            ))

    def _on_tree_select(self, event):
        """Populates form when student row is selected."""
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        self.selected_user_id = int(values[0])
        student = get_student_by_id(self.selected_user_id)
        if not student:
            return

        self.name_var.set(student["full_name"])
        self.roll_var.set(student["roll_no"] or "")
        self.dept_var.set(student["department"] or "")
        self.username_var.set(student["username"])
        self.email_var.set(student["email"] or "")
        self.password_var.set("")  # Clear password field

        # Disallow username editing
        self.entry_username.config(state="disabled")
        self.pass_label.config(text="New Password (optional)")

        self.btn_add.config(state="disabled")
        self.btn_update.config(state="normal")

    def _handle_add(self):
        """Handles creating a new student account."""
        success, msg = create_student(
            full_name=self.name_var.get(),
            username=self.username_var.get(),
            password=self.password_var.get(),
            roll_no=self.roll_var.get(),
            department=self.dept_var.get(),
            email=self.email_var.get(),
            admin_user=self.admin_user
        )

        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_students()
        else:
            messagebox.showerror("Error", msg)

    def _handle_update(self):
        """Handles updating student details."""
        if not self.selected_user_id:
            messagebox.showwarning("Warning", "Please select a student to update.")
            return

        success, msg = update_student(
            user_id=self.selected_user_id,
            full_name=self.name_var.get(),
            roll_no=self.roll_var.get(),
            department=self.dept_var.get(),
            email=self.email_var.get(),
            password=self.password_var.get() if self.password_var.get().strip() else None,
            admin_user=self.admin_user
        )

        if success:
            messagebox.showinfo("Success", msg)
            self._clear_form()
            self.load_students()
        else:
            messagebox.showerror("Error", msg)

    def _clear_form(self):
        """Clears form and resets state."""
        self.selected_user_id = None
        self.name_var.set("")
        self.roll_var.set("")
        self.dept_var.set("")
        self.username_var.set("")
        self.password_var.set("")
        self.email_var.set("")

        self.entry_username.config(state="normal")
        self.pass_label.config(text="Password *")

        self.btn_add.config(state="normal")
        self.btn_update.config(state="disabled")

        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

    def _reset_filters(self):
        self.search_var.set("")
        self.load_students()
