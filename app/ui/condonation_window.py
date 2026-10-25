from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.database.db import get_connection
from app.attendance.service import AttendanceService
from app.ui.reviewer_login import ReviewerLoginWindow


class CondonationWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Condonation Management")
        self.window.geometry("1100x600")
        self.window.minsize(900, 450)

        self.attendance_service = AttendanceService()
        self.reviewer = None

        self._build_ui()
        self.refresh_cases()

    def _build_ui(self):
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)

        main = ttk.Frame(self.window, padding=15)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        ttk.Label(
            main,
            text="Condonation Management",
            font=("Arial", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        ttk.Label(
            main,
            text="Create cases and review pending condonation requests.",
        ).grid(row=1, column=0, sticky="w", pady=(0, 12))

        table_frame = ttk.Frame(main)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = (
            "case_id",
            "roll_no",
            "student_name",
            "percentage",
            "reason",
            "decision",
            "reviewer",
            "created_at",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            selectmode="browse",
        )

        headings = {
            "case_id": "Case ID",
            "roll_no": "Roll Number",
            "student_name": "Student Name",
            "percentage": "Attendance %",
            "reason": "Reason / Reference",
            "decision": "Decision",
            "reviewer": "Reviewed By",
            "created_at": "Created At",
        }

        widths = {
            "case_id": 65,
            "roll_no": 100,
            "student_name": 140,
            "percentage": 100,
            "reason": 200,
            "decision": 95,
            "reviewer": 100,
            "created_at": 160,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                minwidth=60,
                anchor="center",
                stretch=True,
            )

        scrollbar_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        scrollbar_x = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        buttons = ttk.Frame(main)
        buttons.grid(row=3, column=0, sticky="ew", pady=(12, 0))

        ttk.Button(
            buttons,
            text="Create Condonation Case",
            command=self.create_case,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.refresh_cases,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Reviewer Login",
            command=self.login_reviewer,
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Approve Selected",
            command=lambda: self.review_case("approved"),
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Reject Selected",
            command=lambda: self.review_case("rejected"),
        ).pack(side="left")

        ttk.Button(
            buttons,
            text="Close",
            command=self.window.destroy,
        ).pack(side="right")

        self.reviewer_label = ttk.Label(
            main,
            text="Reviewer: Not logged in",
        )
        self.reviewer_label.grid(
            row=4,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

    def refresh_cases(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        connection = None

        try:
            connection = get_connection()

            rows = connection.execute(
                """
                SELECT
                    c.case_id,
                    s.roll_no,
                    s.name,
                    c.percentage,
                    c.reason_reference,
                    c.decision,
                    u.username AS reviewer_username,
                    c.created_at
                FROM condonation AS c
                JOIN students AS s
                    ON s.student_id = c.student_id
                LEFT JOIN users AS u
                    ON u.user_id = c.reviewed_by
                ORDER BY c.created_at DESC, c.case_id DESC
                """
            ).fetchall()

            for row in rows:
                self.tree.insert(
                    "",
                    "end",
                    iid=str(row["case_id"]),
                    values=(
                        row["case_id"],
                        row["roll_no"],
                        row["name"],
                        f"{row['percentage']:.2f}%",
                        row["reason_reference"] or "",
                        row["decision"].capitalize(),
                        row["reviewer_username"] or "",
                        row["created_at"],
                    ),
                )

        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not load condonation cases:\n{exc}",
                parent=self.window,
            )

        finally:
            if connection is not None:
                connection.close()

    def create_case(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Condonation Case")
        dialog.geometry("500x330")
        dialog.resizable(False, False)
        dialog.transient(self.window)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Select Student",
        ).grid(row=0, column=0, sticky="w", pady=8)

        connection = None

        try:
            connection = get_connection()
            students = connection.execute(
                """
                SELECT student_id, roll_no, name
                FROM students
                ORDER BY roll_no
                """
            ).fetchall()

        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not load students:\n{exc}",
                parent=dialog,
            )
            dialog.destroy()
            return

        finally:
            if connection is not None:
                connection.close()

        if not students:
            messagebox.showinfo(
                "No Students",
                "Register a student before creating a condonation case.",
                parent=dialog,
            )
            dialog.destroy()
            return

        student_map = {
            f"{row['roll_no']} - {row['name']}": row["student_id"]
            for row in students
        }

        student_var = tk.StringVar(value=list(student_map.keys())[0])

        student_combo = ttk.Combobox(
            frame,
            textvariable=student_var,
            values=list(student_map.keys()),
            state="readonly",
            width=35,
        )
        student_combo.grid(row=0, column=1, sticky="ew", pady=8)

        ttk.Label(
            frame,
            text="Current Attendance",
        ).grid(row=1, column=0, sticky="w", pady=8)

        percentage_var = tk.StringVar(value="Calculating...")

        ttk.Label(
            frame,
            textvariable=percentage_var,
        ).grid(row=1, column=1, sticky="w", pady=8)

        ttk.Label(
            frame,
            text="Reason / Reference",
        ).grid(row=2, column=0, sticky="w", pady=8)

        reason_var = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=reason_var,
            width=37,
        ).grid(row=2, column=1, sticky="ew", pady=8)

        def update_percentage(*_):
            student_id = student_map.get(student_var.get())

            if student_id is None:
                percentage_var.set("Unavailable")
                return

            try:
                summary = self.attendance_service.get_student_attendance(
                    student_id
                )
                percentage_var.set(
                    f"{summary['percentage']:.2f}% "
                    f"({summary['present_sessions']}/"
                    f"{summary['total_sessions']} sessions)"
                )
            except Exception as exc:
                percentage_var.set("Unavailable")
                messagebox.showerror(
                    "Attendance Error",
                    f"Could not calculate attendance:\n{exc}",
                    parent=dialog,
                )

        student_combo.bind(
            "<<ComboboxSelected>>",
            update_percentage,
        )
        update_percentage()

        def save_case():
            student_id = student_map.get(student_var.get())

            if student_id is None:
                messagebox.showerror(
                    "Invalid Student",
                    "Please select a valid student.",
                    parent=dialog,
                )
                return

            connection = None

            try:
                summary = self.attendance_service.get_student_attendance(
                    student_id
                )
                percentage = float(summary["percentage"])

                connection = get_connection()
                connection.execute(
                    """
                    INSERT INTO condonation (
                        student_id,
                        percentage,
                        reason_reference,
                        decision
                    )
                    VALUES (?, ?, ?, 'pending')
                    """,
                    (
                        student_id,
                        percentage,
                        reason_var.get().strip() or None,
                    ),
                )
                connection.commit()

                messagebox.showinfo(
                    "Case Created",
                    "Condonation case created with Pending status.",
                    parent=dialog,
                )
                dialog.destroy()
                self.refresh_cases()

            except Exception as exc:
                messagebox.showerror(
                    "Save Error",
                    f"Could not create condonation case:\n{exc}",
                    parent=dialog,
                )

            finally:
                if connection is not None:
                    connection.close()

        buttons = ttk.Frame(frame)
        buttons.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(20, 0),
        )

        ttk.Button(
            buttons,
            text="Save Case",
            command=save_case,
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Cancel",
            command=dialog.destroy,
        ).pack(side="left", padx=5)

    def login_reviewer(self):
        ReviewerLoginWindow(
            self.window,
            self._on_reviewer_login,
        )

    def _on_reviewer_login(self, user):
        self.reviewer = user
        self.reviewer_label.configure(
            text=f"Reviewer: {user['username']} ({user['role']})"
        )

        messagebox.showinfo(
            "Login Successful",
            f"Logged in as {user['username']}.",
            parent=self.window,
        )

    def review_case(self, decision):
        if decision not in {"approved", "rejected"}:
            messagebox.showerror(
                "Invalid Decision",
                "Choose approve or reject.",
                parent=self.window,
            )
            return

        if self.reviewer is None:
            messagebox.showwarning(
                "Login Required",
                "Please log in as a reviewer before reviewing a case.",
                parent=self.window,
            )
            return

        if self.reviewer.get("role") != "reviewer":
            messagebox.showerror(
                "Access Denied",
                "Only authenticated reviewers can approve or reject cases.",
                parent=self.window,
            )
            return
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "No Case Selected",
                "Select a condonation case from the table first.",
                parent=self.window,
            )
            return

        case_id = int(selected[0])

        confirm = messagebox.askyesno(
            "Confirm Decision",
            f"Are you sure you want to {decision} case {case_id}?",
            parent=self.window,
        )

        if not confirm:
            return

        connection = None

        try:
            connection = get_connection()

            cursor = connection.execute(
                """
                UPDATE condonation
                SET decision = ?, reviewed_by = ?
                WHERE case_id = ? AND decision = 'pending'
                """,
                (
                    decision,
                    self.reviewer["user_id"],
                    case_id,
                ),
            )

            connection.commit()

            if cursor.rowcount == 0:
                messagebox.showwarning(
                    "Case Not Updated",
                    "This case is no longer pending or does not exist.",
                    parent=self.window,
                )
            else:
                messagebox.showinfo(
                    "Decision Saved",
                    f"Case {case_id} was {decision}.",
                    parent=self.window,
                )

            self.refresh_cases()

        except Exception as exc:
            if connection is not None:
                connection.rollback()

            messagebox.showerror(
                "Review Error",
                f"Could not save the decision:\n{exc}",
                parent=self.window,
            )

        finally:
            if connection is not None:
                connection.close()
