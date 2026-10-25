
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pandas as pd

from app.database.db import get_connection


class SessionReportWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TRISENSE - Session-wise Attendance Report")
        self.window.geometry("1050x550")
        self.window.minsize(850, 450)

        self.sessions = []
        self.selected_session_id = None

        self._build_ui()
        self.load_sessions()

    def _build_ui(self):
        main = ttk.Frame(self.window, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Session-wise Attendance Report",
            font=("Arial", 18, "bold"),
        ).pack(pady=(0, 15))

        selection = ttk.Frame(main)
        selection.pack(fill="x", pady=(0, 12))

        ttk.Label(
            selection,
            text="Select Session:",
        ).pack(side="left", padx=(0, 8))

        self.session_var = tk.StringVar()

        self.session_combo = ttk.Combobox(
            selection,
            textvariable=self.session_var,
            state="readonly",
            width=65,
        )
        self.session_combo.pack(side="left", padx=(0, 8))
        self.session_combo.bind(
            "<<ComboboxSelected>>",
            self.on_session_selected,
        )

        ttk.Button(
            selection,
            text="Load Report",
            command=self.load_report,
        ).pack(side="left")

        columns = (
            "attendance_id",
            "roll_no",
            "name",
            "status",
            "marked_at",
            "confidence",
        )

        self.tree = ttk.Treeview(
            main,
            columns=columns,
            show="headings",
            height=14,
        )

        headings = {
            "attendance_id": "Attendance ID",
            "roll_no": "Roll Number",
            "name": "Student Name",
            "status": "Status",
            "marked_at": "Marked At",
            "confidence": "Recognition Distance",
        }

        widths = {
            "attendance_id": 110,
            "roll_no": 130,
            "name": 200,
            "status": 100,
            "marked_at": 180,
            "confidence": 180,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        scrollbar = ttk.Scrollbar(
            main,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(side="right", fill="y")

        bottom = ttk.Frame(self.window, padding=(20, 0, 20, 15))
        bottom.pack(fill="x")

        self.status_label = ttk.Label(
            bottom,
            text="Select a session to view its attendance.",
        )
        self.status_label.pack(side="left")

        ttk.Button(
            bottom,
            text="Refresh Sessions",
            command=self.load_sessions,
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            bottom,
            text="Export to Excel",
            command=self.export_to_excel,
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            bottom,
            text="Close",
            command=self.window.destroy,
        ).pack(side="right")

    def load_sessions(self):
        try:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        sessions.session_id,
                        subjects.code,
                        subjects.name,
                        subjects.semester,
                        sessions.date,
                        sessions.start_time
                    FROM sessions
                    JOIN subjects
                        ON sessions.subject_id = subjects.subject_id
                    ORDER BY sessions.date DESC, sessions.session_id DESC
                    """
                ).fetchall()

            self.sessions = [dict(row) for row in rows]

            labels = [
                (
                    f"Session {row['session_id']} | "
                    f"{row['code']} - {row['name']} | "
                    f"Semester {row['semester']} | "
                    f"{row['date']} {row['start_time']}"
                )
                for row in self.sessions
            ]

            self.session_combo["values"] = labels

            if labels:
                self.session_combo.current(0)
                self.on_session_selected()
            else:
                self.selected_session_id = None
                self.tree.delete(*self.tree.get_children())
                self.status_label.config(text="No sessions found.")

        except Exception as exc:
            messagebox.showerror(
                "Session Report Error",
                str(exc),
                parent=self.window,
            )

    def on_session_selected(self, event=None):
        index = self.session_combo.current()

        if index < 0 or index >= len(self.sessions):
            self.selected_session_id = None
            return

        self.selected_session_id = self.sessions[index]["session_id"]
        self.load_report()

    def load_report(self):
        if self.selected_session_id is None:
            messagebox.showinfo(
                "Session Report",
                "Please select a session first.",
                parent=self.window,
            )
            return

        try:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        attendance.attendance_id,
                        students.roll_no,
                        students.name,
                        attendance.status,
                        attendance.marked_at,
                        attendance.confidence
                    FROM attendance
                    JOIN students
                        ON attendance.student_id = students.student_id
                    WHERE attendance.session_id = ?
                    ORDER BY students.roll_no
                    """,
                    (self.selected_session_id,),
                ).fetchall()

            self.tree.delete(*self.tree.get_children())

            for row in rows:
                confidence = row["confidence"]

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        row["attendance_id"],
                        row["roll_no"],
                        row["name"],
                        row["status"].upper(),
                        row["marked_at"],
                        (
                            f"{confidence:.4f}"
                            if confidence is not None
                            else "N/A"
                        ),
                    ),
                )

            self.status_label.config(
                text=(
                    f"Session ID: {self.selected_session_id} | "
                    f"Attendance records: {len(rows)}"
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Session Report Error",
                str(exc),
                parent=self.window,
            )

    def export_to_excel(self):
        if self.selected_session_id is None:
            messagebox.showinfo(
                "Export Attendance",
                "Please select a session first.",
                parent=self.window,
            )
            return

        try:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        sessions.session_id,
                        subjects.code AS subject_code,
                        subjects.name AS subject_name,
                        subjects.semester,
                        sessions.date AS session_date,
                        students.roll_no,
                        students.name AS student_name,
                        attendance.status,
                        attendance.marked_at,
                        attendance.confidence
                    FROM sessions
                    JOIN subjects
                        ON sessions.subject_id = subjects.subject_id
                    LEFT JOIN attendance
                        ON sessions.session_id = attendance.session_id
                    LEFT JOIN students
                        ON attendance.student_id = students.student_id
                    WHERE sessions.session_id = ?
                    ORDER BY students.roll_no
                    """,
                    (self.selected_session_id,),
                ).fetchall()

            if not rows:
                messagebox.showinfo(
                    "Export Attendance",
                    "No data is available for this session.",
                    parent=self.window,
                )
                return

            data = []

            for row in rows:
                confidence = row["confidence"]

                data.append({
                    "Session ID": row["session_id"],
                    "Subject Code": row["subject_code"],
                    "Subject Name": row["subject_name"],
                    "Semester": row["semester"],
                    "Session Date": row["session_date"],
                    "Roll Number": row["roll_no"] or "",
                    "Student Name": row["student_name"] or "",
                    "Status": (
                        row["status"].upper()
                        if row["status"]
                        else "NO RECORD"
                    ),
                    "Marked At": row["marked_at"] or "",
                    "Recognition Distance": confidence,
                })

            file_path = filedialog.asksaveasfilename(
                parent=self.window,
                title="Save Session Attendance Report",
                defaultextension=".xlsx",
                filetypes=[("Excel Workbook", "*.xlsx")],
                initialfile=(
                    f"TRISENSE_Session_{self.selected_session_id}_Report.xlsx"
                ),
            )

            if not file_path:
                return

            df = pd.DataFrame(data)

            with pd.ExcelWriter(
                file_path,
                engine="openpyxl",
            ) as writer:
                df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Session Attendance",
                )

                worksheet = writer.sheets["Session Attendance"]

                for column_cells in worksheet.columns:
                    max_length = max(
                        len(str(cell.value))
                        if cell.value is not None
                        else 0
                        for cell in column_cells
                    )
                    worksheet.column_dimensions[
                        column_cells[0].column_letter
                    ].width = min(max_length + 3, 40)

                worksheet.freeze_panes = "A2"
                worksheet.auto_filter.ref = worksheet.dimensions

            messagebox.showinfo(
                "Export Successful",
                f"Session report saved to:\n{file_path}",
                parent=self.window,
            )

        except Exception as exc:
            messagebox.showerror(
                "Export Error",
                str(exc),
                parent=self.window,
            )
