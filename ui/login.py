"""
ui/login.py
Login screen for the College Event Management System.
Provides a modern centered login card with credential verification,
password mask toggling, and role-based redirect callback.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Dict, Any
from auth import authenticate_user
from database import get_connection, init_db, has_any_admin, create_admin_account


class LoginScreen(ttk.Frame):
    """
    Login screen displayed on startup or after logging out.
    """

    def __init__(self, parent: tk.Widget, on_login_success: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success

        self._create_widgets()

    def _create_widgets(self):
        # Background container
        self.configure(style="Main.TFrame")

        # Outer centering frame
        outer_frame = tk.Frame(self, bg="#f1f5f9")
        outer_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Card container with subtle border effect
        card = tk.Frame(outer_frame, bg="#ffffff", bd=1, relief="solid", highlightthickness=0)
        card.pack(padx=20, pady=20, ipadx=30, ipady=30)

        # App Logo & Header
        title_label = tk.Label(
            card,
            text="🎓 College Event Management",
            font=("Segoe UI", 18, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        )
        title_label.pack(pady=(10, 4))

        subtitle_label = tk.Label(
            card,
            text="Sign in to your account (Admin or Student)",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#64748b"
        )
        subtitle_label.pack(pady=(0, 25))

        # Username Field
        user_label = tk.Label(
            card,
            text="Username",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            anchor="w"
        )
        user_label.pack(fill="x", padx=10, pady=(0, 4))

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            card,
            textvariable=self.username_var,
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg="#0f172a",
            bd=1,
            relief="solid"
        )
        self.username_entry.pack(fill="x", padx=10, pady=(0, 15), ipady=5)
        self.username_entry.focus()

        # Password Field
        pass_label = tk.Label(
            card,
            text="Password",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff",
            fg="#1e293b",
            anchor="w"
        )
        pass_label.pack(fill="x", padx=10, pady=(0, 4))

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            card,
            textvariable=self.password_var,
            show="•",
            font=("Segoe UI", 11),
            bg="#f8fafc",
            fg="#0f172a",
            bd=1,
            relief="solid"
        )
        self.password_entry.pack(fill="x", padx=10, pady=(0, 8), ipady=5)

        # Show/Hide password toggle
        self.show_pass_var = tk.BooleanVar(value=False)
        show_pass_chk = tk.Checkbutton(
            card,
            text="Show password",
            variable=self.show_pass_var,
            command=self._toggle_password_visibility,
            bg="#ffffff",
            fg="#475569",
            activebackground="#ffffff",
            font=("Segoe UI", 9)
        )
        show_pass_chk.pack(anchor="w", padx=10, pady=(0, 20))

        # Login Button
        login_btn = tk.Button(
            card,
            text="Sign In",
            command=self._handle_login,
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            padx=15,
            pady=8
        )
        login_btn.pack(fill="x", padx=10, pady=(0, 15))

        # Enter key triggers login
        self.username_entry.bind("<Return>", lambda event: self._handle_login())
        self.password_entry.bind("<Return>", lambda event: self._handle_login())

        # Notice / Default credentials helper
        help_frame = tk.Frame(card, bg="#f1f5f9", bd=1, relief="solid")
        help_frame.pack(fill="x", padx=10, pady=(10, 0), ipadx=8, ipady=8)

        help_title = tk.Label(
            help_frame,
            text="Default Admin Login Details:",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg="#334155"
        )
        help_title.pack(anchor="w")

        help_text = tk.Label(
            help_frame,
            text="Username: admin   |   Password: admin123\nStudents receive login credentials from Admin.",
            font=("Segoe UI", 8),
            bg="#f1f5f9",
            fg="#64748b",
            justify="left"
        )
        help_text.pack(anchor="w", pady=(2, 0))

    def _toggle_password_visibility(self):
        if self.show_pass_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="•")

    def _handle_login(self):
        username = self.username_var.get()
        password = self.password_var.get()

        if not username.strip() or not password.strip():
            messagebox.showwarning("Validation Error", "Please enter both username and password.")
            return

        user_info, message = authenticate_user(username, password, get_connection)

        if user_info:
            # Clear fields upon successful login
            self.password_var.set("")
            self.on_login_success(user_info)
        else:
            messagebox.showerror("Authentication Failed", message)
