
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pandas as pd

from app.database.db import get_connection
from app.attendance.service import AttendanceService


class AttendanceSummaryWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TRISENSE - Attendance Summary")
        self.window.geometry("950x500")
        self.window.minsize(750, 400)

        self.service = AttendanceService()
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="TRISENSE - Student Attendance Summary",
            font=("Arial", 18, "bold"),
        ).pack(pady=(0, 15))

        columns = (
            "student_id",
            "roll_no",
            "name",
            "total",
            "present",
            "absent",
            "percentage",
            "status",
        )

        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=14,
        )

        headings = {
            "student_id": "Student ID",
            "roll_no": "Roll Number",
            "name": "Student Name",
            "total": "Total Sessions",
            "present": "Present",
            "absent": "Absent",
            "percentage": "Attendance %",
            "status": "Status",
        }

        widths = {
            "student_id": 75,
            "roll_no": 105,
            "name": 150,
            "total": 100,
            "present": 80,
            "absent": 80,
            "percentage": 110,
            "status": 100,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree.yview,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Color-coded attendance alerts
        self.tree.tag_configure(
            "good",
            background="#D4EDDA",
            foreground="#155724",
        )
        self.tree.tag_configure(
            "warning",
            background="#FFF3CD",
            foreground="#856404",
        )
        self.tree.tag_configure(
            "low",
            background="#F8D7DA",
            foreground="#721C24",
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True,
        )
        scrollbar.pack(side="right", fill="y")

        bottom = ttk.Frame(self.window, padding=(20, 0, 20, 15))
        bottom.pack(fill="x")

        self.status_label = ttk.Label(bottom, text="")
        self.status_label.pack(side="left")

        ttk.Button(
            bottom,
            text="Refresh",
            command=self.refresh_data,
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

    def refresh_data(self):
        try:
            with get_connection() as conn:
                students = conn.execute(
                    """
                    SELECT student_id, roll_no, name
                    FROM students
                    ORDER BY student_id
                    """
                ).fetchall()

                self.tree.delete(*self.tree.get_children())

                for student in students:
                    summary = self.service.get_student_attendance(
                        student["student_id"]
                    )

                    percentage = summary["percentage"]
                    status = self.service.get_status(percentage)

                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            student["student_id"],
                            student["roll_no"],
                            student["name"],
                            summary["total_sessions"],
                            summary["present_sessions"],
                            summary["absent_sessions"],
                            f"{percentage:.2f}%",
                            status.upper(),
                        ),
                        tags=(status.lower(),),
                    )

            self.status_label.config(
                text=f"Students displayed: {len(students)}"
            )

        except Exception as exc:
            messagebox.showerror(
                "Attendance Summary Error",
                str(exc),
                parent=self.window,
            )

    def export_to_excel(self):
        try:
            rows = []

            with get_connection() as conn:
                students = conn.execute(
                    """
                    SELECT student_id, roll_no, name
                    FROM students
                    ORDER BY student_id
                    """
                ).fetchall()

                for student in students:
                    summary = self.service.get_student_attendance(
                        student["student_id"]
                    )

                    percentage = summary["percentage"]

                    rows.append({
                        "Student ID": student["student_id"],
                        "Roll Number": student["roll_no"],
                        "Student Name": student["name"],
                        "Total Sessions": summary["total_sessions"],
                        "Present": summary["present_sessions"],
                        "Absent": summary["absent_sessions"],
                        "Attendance %": percentage,
                        "Status": self.service.get_status(
                            percentage
                        ).upper(),
                    })

            if not rows:
                messagebox.showinfo(
                    "Export Attendance",
                    "No student records available to export.",
                    parent=self.window,
                )
                return

            file_path = filedialog.asksaveasfilename(
                parent=self.window,
                title="Save Attendance Summary",
                defaultextension=".xlsx",
                filetypes=[("Excel Workbook", "*.xlsx")],
                initialfile="TRISENSE_Attendance_Summary.xlsx",
            )

            if not file_path:
                return

            df = pd.DataFrame(rows)

            with pd.ExcelWriter(
                file_path,
                engine="openpyxl",
            ) as writer:
                df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Attendance",
                )

                worksheet = writer.sheets["Attendance"]

                # Automatically adjust column widths
                for column_cells in worksheet.columns:
                    max_length = max(
                        len(str(cell.value))
                        if cell.value is not None
                        else 0
                        for cell in column_cells
                    )

                    column_letter = column_cells[0].column_letter
                    worksheet.column_dimensions[
                        column_letter
                    ].width = max_length + 3

                # Display attendance percentage to two decimal places
                percentage_column = (
                    list(df.columns).index("Attendance %") + 1
                )

                for row_number in range(
                    2,
                    worksheet.max_row + 1,
                ):
                    worksheet.cell(
                        row=row_number,
                        column=percentage_column,
                    ).number_format = '0.00"%"'

            messagebox.showinfo(
                "Export Successful",
                f"Attendance summary saved to:\n{file_path}",
                parent=self.window,
            )

        except Exception as exc:
            messagebox.showerror(
                "Export Error",
                str(exc),
                parent=self.window,
            )
