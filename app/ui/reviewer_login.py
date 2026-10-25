from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from app.auth.service import AuthenticationService


class ReviewerLoginWindow:
    def __init__(self, parent, on_success):
        self.parent = parent
        self.on_success = on_success

        self.window = tk.Toplevel(parent)
        self.window.title("Reviewer Login")
        self.window.geometry("400x260")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.window, padding=25)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        ttk.Label(
            frame,
            text="Reviewer Login",
            font=("Arial", 16, "bold"),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=(0, 20),
        )

        ttk.Label(
            frame,
            text="Username:",
        ).grid(row=1, column=0, sticky="w", pady=8)

        self.username_var = tk.StringVar()

        username_entry = ttk.Entry(
            frame,
            textvariable=self.username_var,
            width=28,
        )
        username_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=8,
        )

        ttk.Label(
            frame,
            text="Password:",
        ).grid(row=2, column=0, sticky="w", pady=8)

        self.password_var = tk.StringVar()

        password_entry = ttk.Entry(
            frame,
            textvariable=self.password_var,
            show="*",
            width=28,
        )
        password_entry.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=8,
        )

        password_entry.bind("<Return>", lambda _event: self.login())

        buttons = ttk.Frame(frame)
        buttons.grid(
            row=3,
            column=0,
            columnspan=2,
            pady=(20, 0),
        )

        ttk.Button(
            buttons,
            text="Login",
            command=self.login,
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Cancel",
            command=self.window.destroy,
        ).pack(side="left", padx=5)

        username_entry.focus_set()

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Details",
                "Enter both username and password.",
                parent=self.window,
            )
            return

        try:
            user = AuthenticationService().authenticate(
                username,
                password,
            )
        except Exception as exc:
            messagebox.showerror(
                "Login Error",
                f"Could not verify login:\n{exc}",
                parent=self.window,
            )
            return

        if user is None:
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password.",
                parent=self.window,
            )
            self.password_var.set("")
            return

        if user["role"] != "reviewer":
            messagebox.showerror(
                "Access Denied",
                "This account is not authorized to review cases.",
                parent=self.window,
            )
            self.password_var.set("")
            return

        self.password_var.set("")
        self.window.destroy()
        self.on_success(user)
