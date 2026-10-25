from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.attendance.service import AttendanceService
from app.database.db import get_connection


BLACK = "#000000"
PANEL = "#101018"
BLUE = "#398BFF"
GOLD = "#D6A83F"
WHITE = "#F5F5FA"
MUTED = "#85859A"


class StudentCondonationWindow:
    """Allow an authenticated student to submit and view their own requests."""

    def __init__(self, parent, student_id: int):
        self.student_id = int(student_id)
        self.attendance_service = AttendanceService()

        with get_connection() as conn:
            student = conn.execute(
                """
                SELECT student_id, roll_no, name, status
                FROM students
                WHERE student_id = ?
                """,
                (self.student_id,),
            ).fetchone()

        if student is None or student["status"] != "active":
            raise PermissionError("An active student account is required.")

        self.student_name = student["name"]
        self.roll_no = student["roll_no"]

        self.window = tk.Toplevel(parent)
        self.window.title("TRISENSE - My Condonation Requests")
        self.window.geometry("900x600")
        self.window.minsize(700, 450)
        self.window.configure(bg=BLACK)

        self._build_ui()
        self.refresh_requests()

    def _build_ui(self):
        header = tk.Frame(
            self.window,
            bg=BLACK,
            padx=20,
            pady=16,
        )
        header.pack(fill="x")

        tk.Label(
            header,
            text="TRISENSE",
            font=("Segoe UI", 22, "bold"),
            bg=BLACK,
            fg=GOLD,
        ).pack(anchor="w")

        tk.Label(
            header,
            text=f"MY CONDONATION REQUESTS  |  {self.roll_no}",
            font=("Segoe UI", 11, "bold"),
            bg=BLACK,
            fg=BLUE,
        ).pack(anchor="w", pady=(4, 0))

        form = tk.Frame(
            self.window,
            bg=PANEL,
            padx=16,
            pady=12,
        )
        form.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(
            form,
            text="Reason for request",
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg=WHITE,
        ).pack(anchor="w")

        self.reason_text = tk.Text(
            form,
            height=4,
            wrap="word",
            font=("Segoe UI", 10),
            bg="#181824",
            fg=WHITE,
            insertbackground=WHITE,
            relief="flat",
            padx=8,
            pady=8,
        )
        self.reason_text.pack(fill="x", pady=(6, 10))

        tk.Button(
            form,
            text="SUBMIT CONDONATION REQUEST",
            command=self.submit_request,
            font=("Segoe UI", 10, "bold"),
            bg=BLUE,
            fg=BLACK,
            activebackground="#70B5FF",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
        ).pack(anchor="w")

        table_frame = tk.Frame(
            self.window,
            bg=BLACK,
            padx=20,
        )
        table_frame.pack(fill="both", expand=True)

        columns = (
            "case_id",
            "percentage",
            "reason",
            "decision",
            "created_at",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10,
        )

        self.tree.heading("case_id", text="Case ID")
        self.tree.heading("percentage", text="Attendance %")
        self.tree.heading("reason", text="Reason")
        self.tree.heading("decision", text="Decision")
        self.tree.heading("created_at", text="Submitted At")

        self.tree.column("case_id", width=65, anchor="center")
        self.tree.column("percentage", width=110, anchor="center")
        self.tree.column("reason", width=300)
        self.tree.column("decision", width=100, anchor="center")
        self.tree.column("created_at", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        footer = tk.Frame(
            self.window,
            bg=BLACK,
            padx=20,
            pady=12,
        )
        footer.pack(fill="x")

        tk.Button(
            footer,
            text="REFRESH",
            command=self.refresh_requests,
            bg=PANEL,
            fg=WHITE,
            activebackground=BLUE,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
        ).pack(side="left")

        tk.Button(
            footer,
            text="CLOSE",
            command=self.window.destroy,
            bg=PANEL,
            fg=WHITE,
            activebackground=GOLD,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
        ).pack(side="right")

        tk.Label(
            self.window,
            text="Requests and attendance shown here belong only to your account.",
            font=("Segoe UI", 8),
            bg=BLACK,
            fg=MUTED,
        ).pack(pady=(0, 8))

    def refresh_requests(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT case_id, percentage, reason_reference,
                           decision, created_at
                    FROM condonation
                    WHERE student_id = ?
                    ORDER BY created_at DESC, case_id DESC
                    """,
                    (self.student_id,),
                ).fetchall()

            for row in rows:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        row["case_id"],
                        f"{float(row['percentage'] or 0):.2f}%",
                        row["reason_reference"],
                        row["decision"].capitalize(),
                        row["created_at"],
                    ),
                )

        except Exception as exc:
            messagebox.showerror(
                "Load Error",
                f"Could not load your requests:\n{exc}",
                parent=self.window,
            )

    def submit_request(self):
        reason = self.reason_text.get("1.0", "end").strip()

        if not reason:
            messagebox.showwarning(
                "Reason Required",
                "Enter the reason for your condonation request.",
                parent=self.window,
            )
            return

        if len(reason) > 1000:
            messagebox.showwarning(
                "Reason Too Long",
                "Keep the reason within 1000 characters.",
                parent=self.window,
            )
            return

        try:
            summary = self.attendance_service.get_student_attendance(
                self.student_id
            )
            percentage = summary["percentage"]

            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO condonation
                        (student_id, percentage, reason_reference, decision)
                    VALUES (?, ?, ?, 'pending')
                    """,
                    (
                        self.student_id,
                        percentage,
                        reason,
                    ),
                )
                conn.commit()

            self.reason_text.delete("1.0", "end")
            self.refresh_requests()

            messagebox.showinfo(
                "Request Submitted",
                "Your condonation request has been submitted for review.",
                parent=self.window,
            )

        except Exception as exc:
            messagebox.showerror(
                "Submission Error",
                f"Could not submit your request:\n{exc}",
                parent=self.window,
            )
