"""
main.py
Entry point for the College Event Management System (CEMS).
Initializes the SQLite database, configures the Tkinter application,
sets up ttk modern themes, and controls role-based screen routing.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any

from database import init_db
from ui.login import LoginScreen
from ui.admin_dashboard import AdminDashboard
from ui.student_dashboard import StudentDashboard


class CollegeEventManagementApp(tk.Tk):
    """
    Main application window and screen router.
    """

    def __init__(self):
        super().__init__()

        self.title("College Event Management System (CEMS)")
        self.geometry("1100x700")
        self.minsize(960, 620)

        # Center the window on screen
        self._center_window()

        # Session state
        self.current_user: Optional[Dict[str, Any]] = None

        # Container for swappable screens
        self.container = tk.Frame(self, bg="#f1f5f9")
        self.container.pack(fill="both", expand=True)

        # Current active screen reference
        self.current_screen: Optional[tk.Widget] = None

        # Setup ttk styles
        self._setup_styles()

        # Show Login Screen by default
        self.show_login()

    def _center_window(self):
        """Centers the Tkinter window on the primary display."""
        self.update_idletasks()
        width = 1100
        height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2) - 30
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def _setup_styles(self):
        """Configures clean, consistent ttk widget styles."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass  # Fall back to default if clam is unavailable

        # Frame styles
        style.configure("Main.TFrame", background="#f1f5f9")

        # Treeview styling
        style.configure(
            "Treeview",
            background="#ffffff",
            foreground="#0f172a",
            rowheight=28,
            fieldbackground="#ffffff",
            font=("Segoe UI", 9)
        )
        style.map(
            "Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )
        style.configure(
            "Treeview.Heading",
            background="#e2e8f0",
            foreground="#1e293b",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=4
        )

        # Notebook (tabs) styling
        style.configure(
            "TNotebook",
            background="#f1f5f9",
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(16, 8),
            background="#e2e8f0",
            foreground="#334155"
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

        # Combobox styling
        style.configure(
            "TCombobox",
            fieldbackground="#f8fafc",
            background="#ffffff",
            font=("Segoe UI", 9)
        )

    def _clear_container(self):
        """Destroys previous screen widgets."""
        if self.current_screen:
            self.current_screen.destroy()
            self.current_screen = None

    def show_login(self):
        """Displays the login screen."""
        self.current_user = None
        self._clear_container()
        self.current_screen = LoginScreen(self.container, on_login_success=self.on_login_success)
        self.current_screen.pack(fill="both", expand=True)

    def on_login_success(self, user_info: Dict[str, Any]):
        """
        Callback invoked when user successfully logs in.
        Routes to AdminDashboard or StudentDashboard according to user role.
        """
        self.current_user = user_info
        role = user_info.get("role")

        if role == "admin":
            self.show_admin_dashboard()
        elif role == "student":
            self.show_student_dashboard()
        else:
            messagebox.showerror("Error", f"Unrecognized user role: '{role}'.")
            self.show_login()

    def show_admin_dashboard(self):
        """Switches to Admin Dashboard."""
        self._clear_container()
        self.current_screen = AdminDashboard(
            self.container,
            admin_user=self.current_user,
            on_logout=self.show_login
        )
        self.current_screen.pack(fill="both", expand=True)

    def show_student_dashboard(self):
        """Switches to Student Dashboard."""
        self._clear_container()
        self.current_screen = StudentDashboard(
            self.container,
            student_user=self.current_user,
            on_logout=self.show_login
        )
        self.current_screen.pack(fill="both", expand=True)


def main():
    """Main execution function."""
    try:
        # Initialize SQLite database and default admin account
        init_db()
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

    app = CollegeEventManagementApp()
    app.mainloop()


if __name__ == "__main__":
    main()
