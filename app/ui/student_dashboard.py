from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from app.attendance.service import AttendanceService
from app.database.db import get_connection
from app.ui.student_condonation_window import StudentCondonationWindow
from app.ui.student_attendance_calendar import StudentAttendanceCalendar


class StudentDashboard:
    """Dashboard restricted to the authenticated student's own records."""

    def __init__(self, root, user, on_logout):
        if user.get("role") != "student" or not user.get("student_id"):
            raise ValueError("A valid authenticated student is required.")

        self.root = root
        self.user = user
        self.student_id = int(user["student_id"])
        self.on_logout = on_logout
        self.service = AttendanceService()

        self.root.title("TRISENSE - Student Dashboard")
        self.root.configure(bg="#000000")
        self._build_ui()
        self.refresh_attendance()

    def _build_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = tk.Frame(
            self.root,
            bg="#000000",
            padx=30,
            pady=25,
        )
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="TRISENSE",
            font=("Segoe UI", 30, "bold"),
            bg="#000000",
            fg="#FFE7A0",
        ).pack(pady=(0, 5))

        tk.Label(
            frame,
            text="STUDENT DASHBOARD",
            font=("Segoe UI", 12, "bold"),
            bg="#000000",
            fg="#70B5FF",
        ).pack(pady=(0, 20))

        self.identity_label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 11),
            bg="#000000",
            fg="#FF4FA3",
            justify="left",
        )
        self.identity_label.pack(anchor="w", pady=(0, 20))

        summary = tk.LabelFrame(
            frame,
            text=" MY ATTENDANCE ",
            font=("Segoe UI", 11, "bold"),
            bg="#101018",
            fg="#FFE7A0",
            padx=20,
            pady=20,
        )
        summary.pack(fill="x", pady=(0, 20))

        self.attendance_label = tk.Label(
            summary,
            text="Loading attendance...",
            font=("Segoe UI", 13),
            bg="#101018",
            fg="#F5F5FA",
            justify="left",
        )
        self.attendance_label.pack(anchor="w")

        actions = tk.Frame(frame, bg="#000000")
        actions.pack(fill="x", pady=10)

        tk.Button(
            actions,
            text="REFRESH ATTENDANCE",
            command=self.refresh_attendance,
            font=("Segoe UI", 10, "bold"),
            bg="#398BFF",
            fg="#000000",
            activebackground="#70B5FF",
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="MY ATTENDANCE CALENDAR",
            command=self.open_attendance_calendar,
            font=("Segoe UI", 10, "bold"),
            bg="#D6A83F",
            fg="#000000",
            activebackground="#FFE7A0",
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="MY CONDONATION REQUESTS",
            command=self.open_condonation_requests,
            font=("Segoe UI", 10, "bold"),
            bg="#398BFF",
            fg="#000000",
            activebackground="#70B5FF",
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            actions,
            text="LOGOUT",
            command=self.on_logout,
            font=("Segoe UI", 10, "bold"),
            bg="#FF4FA3",
            fg="#000000",
            activebackground="#FFE7A0",
            relief="flat",
            padx=15,
            pady=10,
            cursor="hand2",
        ).pack(side="left")

        tk.Label(
            frame,
            text="TRISENSE • YOUR ATTENDANCE, YOUR RECORD",
            font=("Segoe UI", 9),
            bg="#000000",
            fg="#85859A",
        ).pack(side="bottom", pady=(20, 0))

    def open_attendance_calendar(self):
        try:
            StudentAttendanceCalendar(
                self.root,
                self.student_id,
            )
        except Exception as exc:
            messagebox.showerror(
                "Calendar Error",
                f"Could not open your attendance calendar:\n{exc}",
                parent=self.root,
            )

    def open_condonation_requests(self):
        try:
            StudentCondonationWindow(
                self.root,
                self.student_id,
            )
        except Exception as exc:
            messagebox.showerror(
                "Condonation Error",
                f"Could not open your condonation requests:\n{exc}",
                parent=self.root,
            )

    def refresh_attendance(self):
        try:
            with get_connection() as conn:
                student = conn.execute(
                    """
                    SELECT student_id, roll_no, name, course, semester,
                           section, status
                    FROM students
                    WHERE student_id = ?
                    """,
                    (self.student_id,),
                ).fetchone()

            if student is None or student["status"] != "active":
                messagebox.showerror(
                    "Account Unavailable",
                    "Your student record is missing or inactive. "
                    "Please contact the administrator.",
                    parent=self.root,
                )
                self.on_logout()
                return

            summary = self.service.get_student_attendance(self.student_id)
            percentage = summary["percentage"]
            status = self.service.get_status(percentage).upper()

            self.identity_label.config(
                text=(
                    f"Name: {student['name']}\n"
                    f"Roll Number: {student['roll_no']}\n"
                    f"Course: {student['course'] or '-'}\n"
                    f"Semester: {student['semester'] or '-'}\n"
                    f"Section: {student['section'] or '-'}"
                )
            )

            self.attendance_label.config(
                text=(
                    f"Total recorded sessions: {summary['total_sessions']}\n"
                    f"Present: {summary['present_sessions']}\n"
                    f"Absent: {summary['absent_sessions']}\n"
                    f"Attendance percentage: {percentage:.2f}%\n"
                    f"Attendance status: {status}"
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Attendance Error",
                f"Could not load your attendance:\n{exc}",
                parent=self.root,
            )