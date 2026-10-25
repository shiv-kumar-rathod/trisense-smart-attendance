
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from app.auth.service import AuthenticationService
from app.auth.student_service import StudentAuthenticationService


class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success

        self.root.title("TRISENSE - Login")
        self.root.geometry("1100x680")
        self.root.minsize(900, 580)
        self.root.configure(bg="#101827")
        self.root.resizable(True, True)

        self._background_image = None
        self._background_source = None
        self._resize_job = None

        self._build_ui()

    def _build_ui(self):
        # Canvas keeps the campus image behind all interface elements.
        self.canvas = tk.Canvas(
            self.root,
            bg="#101827",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Load the clean campus photograph.
        background_path = (
            Path(__file__).resolve().parents[2]
            / "assets"
            / "trisense_login_bg.png"
        )

        try:
            from PIL import Image, ImageTk

            self._Image = Image
            self._ImageTk = ImageTk
            self._background_source = Image.open(
                background_path
            ).convert("RGB")

        except Exception as exc:
            self._Image = None
            self._ImageTk = None
            messagebox.showwarning(
                "Background Image",
                "The campus image could not be loaded.\n"
                "The login screen will use a solid background.\n\n"
                f"Details: {exc}",
                parent=self.root,
            )

        # Draw a subtle dark panel behind the branding.
        # It does not cover the whole campus image.
        self.brand_panel = self.canvas.create_rectangle(
            0, 0, 1, 1,
            fill="#101827",
            outline="",
            stipple="gray50",
        )

        # Branding directly on the canvas.
        self.brand_title = self.canvas.create_text(
            0, 0,
            text="TRISENSE",
            anchor="w",
            font=("Segoe UI", 34, "bold"),
            fill="#E5C477",
        )

        self.brand_subtitle = self.canvas.create_text(
            0, 0,
            text="AI-BASED SMART ATTENDANCE",
            anchor="w",
            font=("Segoe UI", 11, "bold"),
            fill="#FFFFFF",
        )

        self.brand_line = self.canvas.create_line(
            0, 0, 0, 0,
            fill="#D5B16B",
            width=3,
        )

        self.brand_headline = self.canvas.create_text(
            0, 0,
            text="Smarter Attendance.\nA Brighter Future.",
            anchor="w",
            justify="left",
            font=("Segoe UI", 25, "bold"),
            fill="#FFFFFF",
        )

        self.brand_description = self.canvas.create_text(
            0, 0,
            text=(
                "A smarter way to manage attendance,\n"
                "powered by intelligent face recognition."
            ),
            anchor="w",
            justify="left",
            font=("Segoe UI", 12),
            fill="#E0E7F0",
        )

        self.brand_quote = self.canvas.create_text(
            0, 0,
            text='"The future depends on what you do today."',
            anchor="w",
            font=("Segoe UI", 11, "italic"),
            fill="#F0CD7A",
        )

        self.brand_quote_author = self.canvas.create_text(
            0, 0,
            text="— Mahatma Gandhi",
            anchor="w",
            font=("Segoe UI", 10),
            fill="#E0E7F0",
        )

        self.brand_credit = self.canvas.create_text(
            0, 0,
            text="PROJECT BY  |  SHIV KUMAR RATHOD",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            fill="#F0CD7A",
        )

        # Login card: a single, deliberately compact panel.
        self.card = tk.Frame(
            self.root,
            bg="#14243B",
            highlightbackground="#C9A45C",
            highlightthickness=2,
            padx=28,
            pady=24,
        )

        tk.Label(
            self.card,
            text="WELCOME BACK",
            font=("Segoe UI", 22, "bold"),
            fg="#FFFFFF",
            bg="#14243B",
        ).pack(anchor="w", pady=(5, 5))

        tk.Label(
            self.card,
            text="Sign in to access your dashboard",
            font=("Segoe UI", 10),
            fg="#C3CEDD",
            bg="#14243B",
        ).pack(anchor="w", pady=(0, 25))

        tk.Label(
            self.card,
            text="USERNAME",
            font=("Segoe UI", 9, "bold"),
            fg="#E5C477",
            bg="#14243B",
        ).pack(anchor="w", pady=(0, 7))

        self.username_var = tk.StringVar()

        self.username_entry = tk.Entry(
            self.card,
            textvariable=self.username_var,
            font=("Segoe UI", 11),
            bg="#F4F6FA",
            fg="#17243A",
            insertbackground="#17243A",
            relief="flat",
            bd=0,
        )
        self.username_entry.pack(
            fill="x",
            ipady=10,
            pady=(0, 18),
        )

        tk.Label(
            self.card,
            text="PASSWORD",
            font=("Segoe UI", 9, "bold"),
            fg="#E5C477",
            bg="#14243B",
        ).pack(anchor="w", pady=(0, 7))

        self.password_var = tk.StringVar()

        self.password_entry = tk.Entry(
            self.card,
            textvariable=self.password_var,
            show="*",
            font=("Segoe UI", 11),
            bg="#F4F6FA",
            fg="#17243A",
            insertbackground="#17243A",
            relief="flat",
            bd=0,
        )
        self.password_entry.pack(
            fill="x",
            ipady=10,
            pady=(0, 23),
        )

        self.password_entry.bind(
            "<Return>",
            lambda _event: self.login(),
        )

        self.login_button = tk.Button(
            self.card,
            text="SIGN IN   →",
            command=self.login,
            font=("Segoe UI", 11, "bold"),
            bg="#D5B16B",
            fg="#101827",
            activebackground="#E8C982",
            activeforeground="#101827",
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=12,
        )
        self.login_button.pack(fill="x", pady=(0, 18))

        tk.Label(
            self.card,
            text="SECURE ACCESS  •  TRISENSE",
            font=("Segoe UI", 8, "bold"),
            fg="#B8C6D8",
            bg="#14243B",
        ).pack(pady=(2, 2))

        # Place the real Tkinter login card on the canvas.
        self.card_window = self.canvas.create_window(
            0, 0,
            window=self.card,
            anchor="center",
            width=390,
        )

        self.canvas.bind(
            "<Configure>",
            self._schedule_layout,
        )

        self.root.after(100, self.username_entry.focus_set)

    def _schedule_layout(self, _event=None):
        # Avoid repeatedly resizing the background during window dragging.
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)

        self._resize_job = self.root.after(
            40,
            self._layout,
        )

    def _layout(self):
        self._resize_job = None

        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)

        # Resize the campus photograph to fill the window.
        if self._background_source is not None:
            try:
                resized = self._background_source.resize(
                    (width, height),
                    self._Image.Resampling.LANCZOS,
                )

                self._background_image = (
                    self._ImageTk.PhotoImage(resized)
                )

                if not hasattr(self, "background_item"):
                    self.background_item = (
                        self.canvas.create_image(
                            0, 0,
                            image=self._background_image,
                            anchor="nw",
                        )
                    )

                self.canvas.itemconfigure(
                    self.background_item,
                    image=self._background_image,
                )

                self.canvas.coords(
                    self.background_item, 0, 0
                )

                self.canvas.tag_lower(self.background_item)

            except Exception:
                pass

        # Keep the branding readable without hiding the whole photo.
        panel_left = width * 0.035
        panel_top = height * 0.08
        panel_right = width * 0.535
        panel_bottom = height * 0.92

        self.canvas.coords(
            self.brand_panel,
            panel_left,
            panel_top,
            panel_right,
            panel_bottom,
        )

        # Position all branding relative to the window size.
        left = width * 0.075
        self.canvas.coords(
            self.brand_title, left, height * 0.20
        )
        self.canvas.coords(
            self.brand_subtitle, left, height * 0.265
        )
        self.canvas.coords(
            self.brand_line,
            left, height * 0.315,
            left + 75, height * 0.315,
        )
        self.canvas.coords(
            self.brand_headline, left, height * 0.40
        )
        self.canvas.coords(
            self.brand_description, left, height * 0.51
        )
        self.canvas.coords(
            self.brand_quote, left, height * 0.64
        )
        self.canvas.coords(
            self.brand_quote_author, left, height * 0.685
        )
        self.canvas.coords(
            self.brand_credit, left, height * 0.86
        )

        # Place the login card on the right.
        card_width = min(390, width * 0.36)
        card_center_x = width * 0.755
        card_center_y = height * 0.50

        self.canvas.coords(
            self.card_window,
            card_center_x,
            card_center_y,
        )
        self.canvas.itemconfigure(
            self.card_window,
            width=int(card_width),
        )

    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Details",
                "Enter both username and password.",
                parent=self.root,
            )
            return

        try:
            user = AuthenticationService().authenticate(
                username,
                password,
            )

            if user is None:
                user = StudentAuthenticationService().authenticate(
                    username,
                    password,
                )

        except Exception as exc:
            messagebox.showerror(
                "Login Error",
                f"Could not verify login:\n{exc}",
                parent=self.root,
            )
            return

        if user is None:
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password.",
                parent=self.root,
            )
            self.password_var.set("")
            return

        if user["role"] not in {
            "admin",
            "reviewer",
            "student",
        }:
            messagebox.showerror(
                "Access Denied",
                "This account is not authorized to access TRISENSE.",
                parent=self.root,
            )
            self.password_var.set("")
            return

        self.password_var.set("")
        self.on_success(user)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Login Window",
        "This login window is launched by the main application.",
        parent=root,
    )
    root.destroy()
