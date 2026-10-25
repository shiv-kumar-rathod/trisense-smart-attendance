from __future__ import annotations

import calendar
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from app.attendance.calendar_service import AttendanceCalendarService


BLACK = "#000000"
PANEL = "#101018"
BLUE = "#398BFF"
GOLD = "#D6A83F"
PINK = "#FF4FA3"
WHITE = "#F5F5FA"
MUTED = "#85859A"
GREEN = "#3DAB70"
RED = "#D9534F"


class StudentAttendanceCalendar:
    """Monthly attendance calendar restricted to one authenticated student."""

    def __init__(self, parent, student_id: int):
        self.student_id = int(student_id)
        self.service = AttendanceCalendarService()

        today = date.today()
        self.year = today.year
        self.month = today.month
        self.selected_date = today.isoformat()
        self.selected_subject_id = None

        self.window = tk.Toplevel(parent)
        self.window.title("TRISENSE - Attendance Calendar")
        self.window.geometry("1100x760")
        self.window.minsize(850, 600)
        self.window.configure(bg=BLACK)

        self.subject_map = {}
        self.calendar_data = {}
        self.summary_data = []

        self._build_ui()
        self._load_subjects()
        self.refresh_calendar()

    def _build_ui(self):
        header = tk.Frame(self.window, bg=BLACK, padx=20, pady=12)
        header.pack(fill="x")

        tk.Label(
            header,
            text="MY ATTENDANCE CALENDAR",
            font=("Segoe UI", 22, "bold"),
            bg=BLACK,
            fg=GOLD,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Review your recorded attendance by date and subject",
            font=("Segoe UI", 10),
            bg=BLACK,
            fg=BLUE,
        ).pack(anchor="w", pady=(4, 0))

        filters = tk.Frame(self.window, bg=BLACK, padx=20, pady=8)
        filters.pack(fill="x")

        tk.Label(
            filters,
            text="Subject:",
            bg=BLACK,
            fg=WHITE,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.subject_var = tk.StringVar(value="All subjects")
        self.subject_combo = ttk.Combobox(
            filters,
            textvariable=self.subject_var,
            state="readonly",
            width=35,
        )
        self.subject_combo.pack(side="left")
        self.subject_combo.bind(
            "<<ComboboxSelected>>",
            self._on_subject_changed,
        )

        tk.Button(
            filters,
            text="REFRESH",
            command=self.refresh_calendar,
            bg=BLUE,
            fg=BLACK,
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
        ).pack(side="left", padx=10)

        body = tk.Frame(self.window, bg=BLACK, padx=20, pady=8)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=PANEL, padx=12, pady=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        navigation = tk.Frame(left, bg=PANEL)
        navigation.pack(fill="x", pady=(0, 10))

        tk.Button(
            navigation,
            text="‹",
            command=lambda: self.change_month(-1),
            bg=PANEL,
            fg=GOLD,
            activebackground=BLUE,
            relief="flat",
            font=("Segoe UI", 16, "bold"),
            width=3,
        ).pack(side="left")

        self.month_label = tk.Label(
            navigation,
            text="",
            font=("Segoe UI", 15, "bold"),
            bg=PANEL,
            fg=WHITE,
        )
        self.month_label.pack(side="left", expand=True)

        tk.Button(
            navigation,
            text="›",
            command=lambda: self.change_month(1),
            bg=PANEL,
            fg=GOLD,
            activebackground=BLUE,
            relief="flat",
            font=("Segoe UI", 16, "bold"),
            width=3,
        ).pack(side="right")

        self.calendar_frame = tk.Frame(left, bg=PANEL)
        self.calendar_frame.pack(fill="both", expand=True)

        legend = tk.Frame(left, bg=PANEL)
        legend.pack(fill="x", pady=(10, 0))

        for color, text in (
            (GREEN, "Present recorded"),
            (RED, "Recorded absent"),
            (GOLD, "Not recorded"),
            (MUTED, "No session"),
        ):
            tk.Label(
                legend,
                text=f"● {text}",
                font=("Segoe UI", 8),
                bg=PANEL,
                fg=color,
            ).pack(anchor="w", pady=1)

        right = tk.Frame(body, bg=PANEL, padx=12, pady=12, width=390)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        tk.Label(
            right,
            text="SELECTED DATE",
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg=GOLD,
        ).pack(anchor="w")

        self.date_label = tk.Label(
            right,
            text="Choose a calendar date",
            font=("Segoe UI", 10),
            bg=PANEL,
            fg=WHITE,
        )
        self.date_label.pack(anchor="w", pady=(5, 12))

        tk.Label(
            right,
            text="Daily sessions",
            font=("Segoe UI", 10, "bold"),
            bg=PANEL,
            fg=BLUE,
        ).pack(anchor="w")

        self.details = tk.Text(
            right,
            height=12,
            wrap="word",
            font=("Segoe UI", 9),
            bg="#181824",
            fg=WHITE,
            insertbackground=WHITE,
            relief="flat",
            padx=8,
            pady=8,
            state="disabled",
        )
        self.details.pack(fill="x", pady=(6, 14))

        tk.Label(
            right,
            text="SUBJECT SUMMARY",
            font=("Segoe UI", 11, "bold"),
            bg=PANEL,
            fg=GOLD,
        ).pack(anchor="w")

        columns = ("subject", "percentage", "status")
        self.summary_tree = ttk.Treeview(
            right,
            columns=columns,
            show="headings",
            height=9,
        )
        self.summary_tree.heading("subject", text="Subject")
        self.summary_tree.heading("percentage", text="Present %")
        self.summary_tree.heading("status", text="Status")

        self.summary_tree.column("subject", width=145)
        self.summary_tree.column(
            "percentage", width=80, anchor="center"
        )
        self.summary_tree.column(
            "status", width=100, anchor="center"
        )

        self.summary_tree.pack(fill="both", expand=True, pady=(6, 0))

        self.summary_tree.tag_configure("low", foreground=RED)
        self.summary_tree.tag_configure("good", foreground=GREEN)
        self.summary_tree.tag_configure("unknown", foreground=GOLD)

        footer = tk.Frame(self.window, bg=BLACK, padx=20, pady=10)
        footer.pack(fill="x")

        tk.Label(
            footer,
            text=(
                "Missing attendance is shown as Not Recorded, "
                "not automatically as Absent."
            ),
            font=("Segoe UI", 9),
            bg=BLACK,
            fg=MUTED,
        ).pack(side="left")

        tk.Button(
            footer,
            text="CLOSE",
            command=self.window.destroy,
            bg=PINK,
            fg=BLACK,
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2",
        ).pack(side="right")

    def _load_subjects(self):
        try:
            subjects = self.service.get_subjects(self.student_id)

            self.subject_map = {"All subjects": None}
            for subject in subjects:
                label = f"{subject['code']} - {subject['name']}"
                self.subject_map[label] = subject["subject_id"]

            self.subject_combo["values"] = list(self.subject_map.keys())
            self.subject_var.set("All subjects")

        except Exception as exc:
            messagebox.showerror(
                "Subject Error",
                f"Could not load subjects:\n{exc}",
                parent=self.window,
            )

    def _on_subject_changed(self, _event=None):
        self.selected_subject_id = self.subject_map.get(
            self.subject_var.get()
        )
        self.refresh_calendar()

    def change_month(self, offset):
        self.month += offset

        if self.month < 1:
            self.month = 12
            self.year -= 1
        elif self.month > 12:
            self.month = 1
            self.year += 1

        self.selected_date = ""
        self.refresh_calendar()

    def refresh_calendar(self):
        try:
            result = self.service.get_month_calendar(
                self.student_id,
                self.year,
                self.month,
                self.selected_subject_id,
            )
            self.calendar_data = result["sessions_by_date"]

            self.summary_data = self.service.get_subject_summaries(
                self.student_id
            )

            self._draw_calendar()
            self._show_selected_date()
            self._draw_summary()

        except Exception as exc:
            messagebox.showerror(
                "Calendar Error",
                f"Could not load attendance calendar:\n{exc}",
                parent=self.window,
            )

    def _draw_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_label.config(
            text=f"{calendar.month_name[self.month]} {self.year}"
        )

        weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

        for column, name in enumerate(weekdays):
            tk.Label(
                self.calendar_frame,
                text=name,
                font=("Segoe UI", 9, "bold"),
                bg=PANEL,
                fg=BLUE,
                width=5,
            ).grid(row=0, column=column, sticky="nsew", padx=2, pady=3)

            self.calendar_frame.grid_columnconfigure(column, weight=1)

        month_grid = calendar.monthcalendar(self.year, self.month)

        for row_index, week in enumerate(month_grid, start=1):
            self.calendar_frame.grid_rowconfigure(row_index, weight=1)

            for column, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        self.calendar_frame,
                        text="",
                        bg=PANEL,
                    ).grid(
                        row=row_index,
                        column=column,
                        sticky="nsew",
                        padx=2,
                        pady=2,
                    )
                    continue

                day_date = date(self.year, self.month, day).isoformat()
                sessions = self.calendar_data.get(day_date, [])

                color = MUTED
                marker = "—"

                if sessions:
                    statuses = {item["status"] for item in sessions}

                    if "present" in statuses:
                        color = GREEN
                        marker = "P"
                    elif "absent" in statuses:
                        color = RED
                        marker = "A"
                    else:
                        color = GOLD
                        marker = "?"

                selected = day_date == self.selected_date

                button = tk.Button(
                    self.calendar_frame,
                    text=f"{day}\n{marker}",
                    command=lambda value=day_date: self.select_date(value),
                    bg="#242432" if selected else "#181824",
                    fg=color,
                    activebackground=BLUE,
                    activeforeground=BLACK,
                    relief="solid" if selected else "flat",
                    bd=1 if selected else 0,
                    font=("Segoe UI", 10, "bold"),
                    cursor="hand2",
                )
                button.grid(
                    row=row_index,
                    column=column,
                    sticky="nsew",
                    padx=2,
                    pady=2,
                    ipady=5,
                )

    def select_date(self, selected_date):
        self.selected_date = selected_date
        self._draw_calendar()
        self._show_selected_date()

    def _show_selected_date(self):
        self.date_label.config(
            text=self.selected_date or "Choose a calendar date"
        )

        self.details.config(state="normal")
        self.details.delete("1.0", "end")

        if not self.selected_date:
            self.details.insert("end", "Select a date to view its sessions.")
        else:
            sessions = self.calendar_data.get(self.selected_date, [])

            if not sessions:
                self.details.insert(
                    "end",
                    "No scheduled sessions found for this date "
                    "under the selected subject filter.",
                )
            else:
                for item in sessions:
                    self.details.insert(
                        "end",
                        f"{item['subject_code']} - {item['subject_name']}\n",
                    )
                    self.details.insert(
                        "end",
                        f"Time: {item['start_time']}"
                        f" - {item['end_time'] or 'Not specified'}\n",
                    )

                    status = item["status"].replace("_", " ").title()
                    self.details.insert("end", f"Status: {status}\n\n")

        self.details.config(state="disabled")

    def _draw_summary(self):
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        for summary in self.summary_data:
            percentage = summary["percentage"]
            unrecorded = summary["unrecorded_sessions"]

            if summary["scheduled_sessions"] == 0:
                status = "No sessions"
                tag = "unknown"
            elif unrecorded > 0:
                status = "Incomplete"
                tag = "unknown"
            elif percentage < 75.0:
                status = "Below 75%"
                tag = "low"
            else:
                status = "OK"
                tag = "good"

            if (
                self.selected_subject_id is not None
                and summary["subject_id"] != self.selected_subject_id
            ):
                continue

            self.summary_tree.insert(
                "",
                "end",
                values=(
                    summary["subject_code"],
                    f"{percentage:.2f}%",
                    status,
                ),
                tags=(tag,),
            )
