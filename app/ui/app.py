from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from config import APP_NAME
from app.database.db import initialize_database
from app.registration.window import RegistrationWindow
from app.attendance.window import AttendanceWindow
from app.ui.attendance_summary import AttendanceSummaryWindow
from app.ui.session_report import SessionReportWindow
from app.ui.condonation_window import CondonationWindow
from app.ui.login_window import LoginWindow
from app.ui.student_dashboard import StudentDashboard
from app.ui.student_account_window import StudentAccountWindow

BLACK = "#000000"
PANEL = "#101018"
BLUE = "#398BFF"
BLUE_GLOW = "#70B5FF"
PINK = "#FF4FA3"
GOLD = "#D6A83F"
GOLD_LIGHT = "#FFE7A0"
WHITE = "#F5F5FA"
MUTED = "#85859A"


class AttendanceApp:
    def __init__(self, require_login=True):
        initialize_database()

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Login")
        self.root.geometry("1100x750")
        self.root.minsize(850, 600)
        self.root.resizable(True, True)

        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        self.root.configure(bg=BLACK)
        self.current_user = None
        self.require_login = require_login

        if self.require_login:
            LoginWindow(self.root, self._on_login_success)
        else:
            self._build_ui()

    def _on_login_success(self, user):
        self.current_user = user

        if user.get("role") == "student":
            try:
                StudentDashboard(
                    self.root,
                    user,
                    self.logout,
                )
                self.root.title(f"{APP_NAME} - Student Dashboard")
                self.root.deiconify()
            except Exception as exc:
                self.current_user = None
                messagebox.showerror(
                    "Student Dashboard Error",
                    f"Could not open the student dashboard:\n{exc}",
                    parent=self.root,
                )
                self.root.withdraw()
                LoginWindow(self.root, self._on_login_success)
            return

        if user.get("role") not in {"admin", "reviewer"}:
            self.current_user = None
            messagebox.showerror(
                "Access Denied",
                "This account is not authorized to access this dashboard.",
                parent=self.root,
            )
            self.root.withdraw()
            LoginWindow(self.root, self._on_login_success)
            return

        self._build_ui()
        self.root.title(f"{APP_NAME} - Dashboard")
        self.root.deiconify()

    def _make_button(self, parent, text, command, accent=GOLD):
        border = tk.Frame(parent, bg=accent, padx=1, pady=1)
        border.pack(fill="x", pady=5)

        button = tk.Button(
            border,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg=GOLD_LIGHT if accent == GOLD else WHITE,
            activebackground=accent,
            activeforeground=BLACK,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=20,
            pady=9,
            anchor="center",
            highlightthickness=0,
        )
        button.pack(fill="x")

        def on_enter(event):
            button.configure(bg=accent, fg=BLACK)
            border.configure(
                bg=GOLD_LIGHT if accent == GOLD else WHITE
            )

        def on_leave(event):
            button.configure(
                bg=PANEL,
                fg=GOLD_LIGHT if accent == GOLD else WHITE,
            )
            border.configure(bg=accent)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        return border

    def _build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=BLACK)

        outer = tk.Frame(self.root, bg=BLACK)
        outer.pack(fill="both", expand=True)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_rowconfigure(2, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        content = tk.Frame(
            outer,
            bg=BLACK,
            padx=30,
            pady=20,
        )
        content.grid(row=1, column=0)

        tk.Label(
            content,
            text="TRISENSE",
            font=("Segoe UI", 34, "bold"),
            bg=BLACK,
            fg=GOLD_LIGHT,
        ).pack(pady=(0, 3))

        accent_line = tk.Frame(content, bg=BLACK)
        accent_line.pack(pady=(5, 16))

        tk.Frame(
            accent_line, bg=BLUE, height=3, width=85
        ).pack(side="left")
        tk.Frame(
            accent_line, bg=PINK, height=3, width=35
        ).pack(side="left")
        tk.Frame(
            accent_line, bg=GOLD, height=3, width=35
        ).pack(side="left")

        tk.Label(
            content,
            text="SMART ATTENDANCE MANAGEMENT SYSTEM",
            font=("Segoe UI", 11, "bold"),
            bg=BLACK,
            fg=BLUE_GLOW,
        ).pack(pady=(0, 14))

        if self.current_user:
            tk.Label(
                content,
                text=(
                    f"{self.current_user['username']}  |  "
                    f"{self.current_user['role'].capitalize()}"
                ),
                font=("Segoe UI", 10),
                bg=BLACK,
                fg=PINK,
            ).pack(pady=(0, 15))

        role = (
            self.current_user["role"]
            if self.current_user
            else "admin"
        )

        buttons = tk.Frame(content, bg=BLACK)
        buttons.pack(fill="x")

        if role == "admin":
            self._make_button(
                buttons,
                "01   STUDENT REGISTRATION",
                self.open_registration,
                BLUE,
            )

            self._make_button(
                buttons,
                "02   STUDENT ACCOUNT MANAGEMENT",
                self.open_student_account_management,
                PINK,
            )

            self._make_button(
                buttons,
                "03   START ATTENDANCE",
                self.open_attendance,
                GOLD,
            )

            self._make_button(
                buttons,
                "04   ATTENDANCE SUMMARY",
                self.open_attendance_summary,
                BLUE,
            )

            self._make_button(
                buttons,
                "05   SESSION-WISE REPORT",
                self.open_session_report,
                PINK,
            )

            self._make_button(
                buttons,
                "06   CONDONATION MANAGEMENT",
                self.open_condonation,
                GOLD,
            )

        elif role == "reviewer":
            self._make_button(
                buttons,
                "CONDONATION MANAGEMENT",
                self.open_condonation,
                GOLD,
            )

        if self.current_user:
            self._make_button(
                buttons,
                "LOGOUT",
                self.logout,
                PINK,
            )

        self._make_button(
            buttons,
            "EXIT APPLICATION",
            self.root.destroy,
            PINK,
        )

        tk.Label(
            content,
            text="TRISENSE  •  SMARTER ATTENDANCE",
            font=("Segoe UI", 8),
            bg=BLACK,
            fg=MUTED,
        ).pack(pady=(16, 0))

        tk.Label(
            content,
            text="Developed by SHIV KUMAR RATHOD",
            font=("Segoe UI", 8),
            bg=BLACK,
            fg="#777788",
        ).pack(pady=(4, 0))

    def open_registration(self):
        if not self._require_role("admin"):
            return

        RegistrationWindow(self.root)

    def open_student_account_management(self):
        if not self._require_role("admin"):
            return

        StudentAccountWindow(
            self.root,
            self.current_user,
        )

    def open_attendance(self):
        if not self._require_role("admin"):
            return

        AttendanceWindow(self.root)

    def open_attendance_summary(self):
        if not self._require_role("admin"):
            return

        AttendanceSummaryWindow(self.root)

    def open_session_report(self):
        if not self._require_role("admin"):
            return

        SessionReportWindow(self.root)

    def open_condonation(self):
        if not self._require_role("admin", "reviewer"):
            return

        CondonationWindow(self.root)

    def _require_role(self, *allowed_roles):
        if not self.current_user:
            messagebox.showerror(
                "Access Denied",
                "Please log in first.",
                parent=self.root,
            )
            return False

        if self.current_user.get("role") not in allowed_roles:
            messagebox.showerror(
                "Access Denied",
                "Your account is not authorized for this feature.",
                parent=self.root,
            )
            return False

        return True

    def logout(self):
        self.current_user = None
        self.root.title(f"{APP_NAME} - Login")

        for widget in self.root.winfo_children():
            widget.destroy()

        LoginWindow(self.root, self._on_login_success)
        self.root.deiconify()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AttendanceApp().run()