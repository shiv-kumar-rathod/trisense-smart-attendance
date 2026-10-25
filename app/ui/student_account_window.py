from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.auth.student_service import StudentAuthenticationService
from app.database.db import get_connection


class StudentAccountWindow:
    """Allow administrators to manage student login account creation and viewing."""

    def __init__(self, parent, admin_user):
        if not admin_user or admin_user.get("role") != "admin":
            raise PermissionError("Only an administrator can manage student accounts.")

        self.admin_user = admin_user
        self.window = tk.Toplevel(parent)
        self.window.title("TRISENSE - Student Account Management")
        self.window.geometry("1050x650")
        self.window.minsize(850, 520)

        self.student_map = {}
        self._build_ui()
        self._load_students()
        self._load_accounts()

    def _build_ui(self):
        outer = ttk.Frame(self.window, padding=14)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(
            outer, text="Create Student Login Account", padding=12
        )
        form.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Registered student:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(
            form, textvariable=self.student_var, state="readonly"
        )
        self.student_combo.grid(
            row=0, column=1, sticky="ew", padx=(0, 16), pady=5
        )

        ttk.Label(form, text="Username:").grid(
            row=0, column=2, sticky="w", padx=(0, 8), pady=5
        )
        self.username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.username_var).grid(
            row=0, column=3, sticky="ew", pady=5
        )

        ttk.Label(form, text="Password (12+ characters):").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.password_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.password_var, show="*").grid(
            row=1, column=1, sticky="ew", padx=(0, 16), pady=5
        )

        ttk.Label(form, text="Confirm password:").grid(
            row=1, column=2, sticky="w", padx=(0, 8), pady=5
        )
        self.confirm_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.confirm_var, show="*").grid(
            row=1, column=3, sticky="ew", pady=5
        )

        ttk.Label(
            form,
            text="Each registered student can have only one account.",
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 2))

        form_buttons = ttk.Frame(form)
        form_buttons.grid(row=3, column=0, columnspan=4, sticky="e", pady=(8, 0))
        ttk.Button(
            form_buttons, text="Create Account", command=self.create_account
        ).pack(side="left", padx=4)
        ttk.Button(
            form_buttons, text="Refresh Students", command=self._refresh_all
        ).pack(side="left", padx=4)

        accounts_frame = ttk.LabelFrame(
            outer, text="Existing Student Accounts", padding=10
        )
        accounts_frame.grid(row=1, column=0, sticky="nsew")
        accounts_frame.columnconfigure(0, weight=1)
        accounts_frame.rowconfigure(0, weight=1)

        columns = ("roll_no", "name", "username", "created_at")
        self.accounts_tree = ttk.Treeview(
            accounts_frame, columns=columns, show="headings", height=12
        )
        self.accounts_tree.heading("roll_no", text="Roll Number")
        self.accounts_tree.heading("name", text="Student Name")
        self.accounts_tree.heading("username", text="Username")
        self.accounts_tree.heading("created_at", text="Account Created")

        self.accounts_tree.column("roll_no", width=140, anchor="center")
        self.accounts_tree.column("name", width=240)
        self.accounts_tree.column("username", width=220)
        self.accounts_tree.column("created_at", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(
            accounts_frame, orient="vertical", command=self.accounts_tree.yview
        )
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        self.accounts_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        bottom = ttk.Frame(outer)
        bottom.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.account_count_var = tk.StringVar(value="Existing accounts: 0")
        ttk.Label(bottom, textvariable=self.account_count_var).pack(side="left")
        ttk.Button(
            bottom, text="Refresh Accounts", command=self._load_accounts
        ).pack(side="right", padx=4)
        ttk.Button(
            bottom, text="Close", command=self.window.destroy
        ).pack(side="right", padx=4)

    def _refresh_all(self):
        self._load_students()
        self._load_accounts()

    def _load_students(self):
        try:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT s.student_id, s.roll_no, s.name
                    FROM students AS s
                    LEFT JOIN student_accounts AS sa
                        ON sa.student_id = s.student_id
                    WHERE s.status = 'active'
                      AND sa.account_id IS NULL
                    ORDER BY s.roll_no
                    """
                ).fetchall()

            self.student_map = {
                f"{row['roll_no']} - {row['name']}": row["student_id"]
                for row in rows
            }
            self.student_combo["values"] = list(self.student_map.keys())
            self.student_var.set(next(iter(self.student_map), ""))

            if not rows:
                self.student_var.set("")
        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not load eligible students:\n{exc}",
                parent=self.window,
            )

    def _load_accounts(self):
        try:
            with get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT s.roll_no, s.name, sa.username, sa.created_at
                    FROM student_accounts AS sa
                    JOIN students AS s ON s.student_id = sa.student_id
                    ORDER BY s.roll_no
                    """
                ).fetchall()

            for item in self.accounts_tree.get_children():
                self.accounts_tree.delete(item)

            for row in rows:
                self.accounts_tree.insert(
                    "",
                    "end",
                    values=(
                        row["roll_no"],
                        row["name"],
                        row["username"],
                        row["created_at"],
                    ),
                )

            self.account_count_var.set(f"Existing accounts: {len(rows)}")
        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not load existing accounts:\n{exc}",
                parent=self.window,
            )

    def create_account(self):
        selected_student = self.student_var.get()
        student_id = self.student_map.get(selected_student)
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirmation = self.confirm_var.get()

        if student_id is None:
            messagebox.showwarning(
                "Select Student",
                "Select an eligible registered student.",
                parent=self.window,
            )
            return

        if not username:
            messagebox.showwarning(
                "Missing Username",
                "Enter a username.",
                parent=self.window,
            )
            return

        if len(password) < 12:
            messagebox.showwarning(
                "Weak Password",
                "The password must contain at least 12 characters.",
                parent=self.window,
            )
            return

        if password != confirmation:
            messagebox.showerror(
                "Password Mismatch",
                "The passwords do not match.",
                parent=self.window,
            )
            return

        try:
            account_id = StudentAuthenticationService().create_student_account(
                student_id=student_id,
                username=username,
                password=password,
            )

            self.password_var.set("")
            self.confirm_var.set("")
            self.username_var.set("")

            messagebox.showinfo(
                "Account Created",
                f"Student login account created successfully.\nAccount ID: {account_id}",
                parent=self.window,
            )
            self._refresh_all()

        except ValueError as exc:
            messagebox.showerror(
                "Account Creation Failed",
                str(exc),
                parent=self.window,
            )
        except Exception as exc:
            messagebox.showerror(
                "Unexpected Error",
                f"Could not create the account:\n{exc}",
                parent=self.window,
            )
