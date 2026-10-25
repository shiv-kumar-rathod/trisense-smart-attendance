from __future__ import annotations

import cv2
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

from app.attendance.live_service import LiveAttendanceService
from app.attendance.session_service import AttendanceSessionService


class AttendanceWindow:
    def __init__(self, parent):
        self.parent = parent

        self.window = tk.Toplevel(parent)
        self.window.title("Start Attendance")
        self.window.geometry("600x500")
        self.window.resizable(False, False)

        self.camera = None
        self.latest_frame = None
        self.camera_running = False
        self.session_id = None
        self.subject_id = None

        self.service = LiveAttendanceService(
            tolerance=0.65
        )

        self._build_ui()

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close,
        )

    def _build_ui(self):
        frame = ttk.Frame(
            self.window,
            padding=20,
        )
        frame.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            frame,
            text="Attendance Session",
            font=("Arial", 18, "bold"),
        ).pack(pady=(0, 20))

        form = ttk.Frame(frame)
        form.pack(fill="x")

        ttk.Label(
            form,
            text="Subject Code:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=5,
        )

        self.code_entry = ttk.Entry(
            form,
            width=35,
        )
        self.code_entry.grid(
            row=0,
            column=1,
            padx=10,
            pady=5,
        )

        ttk.Label(
            form,
            text="Subject Name:",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=5,
        )

        self.name_entry = ttk.Entry(
            form,
            width=35,
        )
        self.name_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=5,
        )

        ttk.Label(
            form,
            text="Semester:",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=5,
        )

        self.semester_entry = ttk.Entry(
            form,
            width=35,
        )
        self.semester_entry.grid(
            row=2,
            column=1,
            padx=10,
            pady=5,
        )

        ttk.Button(
            form,
            text="Start Session",
            command=self.start_session,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            pady=15,
        )

        self.session_label = ttk.Label(
            frame,
            text="No active session",
        )
        self.session_label.pack(pady=5)

        self.status_label = ttk.Label(
            frame,
            text="Create a session to begin.",
        )
        self.status_label.pack(pady=5)

        buttons = ttk.Frame(frame)
        buttons.pack(pady=15)

        self.camera_button = ttk.Button(
            buttons,
            text="Start Camera",
            command=self.start_camera,
            state="disabled",
        )
        self.camera_button.grid(
            row=0,
            column=0,
            padx=5,
        )

        self.scan_button = ttk.Button(
            buttons,
            text="Scan Face",
            command=self.scan_face,
            state="disabled",
        )
        self.scan_button.grid(
            row=0,
            column=1,
            padx=5,
        )

        ttk.Button(
            buttons,
            text="Stop Camera",
            command=self.stop_camera,
        ).grid(
            row=0,
            column=2,
            padx=5,
        )

        ttk.Button(
            frame,
            text="Close",
            command=self.close,
        ).pack(pady=10)

    def start_session(self):
        code = self.code_entry.get().strip()
        name = self.name_entry.get().strip()
        semester = self.semester_entry.get().strip()

        if not code:
            messagebox.showerror(
                "Validation Error",
                "Subject code is required.",
                parent=self.window,
            )
            return

        if not name:
            messagebox.showerror(
                "Validation Error",
                "Subject name is required.",
                parent=self.window,
            )
            return

        try:
            self.subject_id = (
                AttendanceSessionService.create_subject(
                    code,
                    name,
                    semester or None,
                )
            )

            now = datetime.now()

            self.session_id = (
                AttendanceSessionService.create_session(
                    self.subject_id,
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S"),
                )
            )

            loaded = self.service.load_registered_faces()

            if loaded <= 0:
                raise RuntimeError(
                    "No registered face embeddings were found."
                )

            self.session_label.config(
                text=f"Active session: {self.session_id}"
            )

            self.status_label.config(
                text=f"Session ready. Registered embeddings: {loaded}"
            )

            self.camera_button.config(
                state="normal"
            )

        except Exception as exc:
            messagebox.showerror(
                "Session Error",
                str(exc),
                parent=self.window,
            )

    def start_camera(self):
        if self.camera_running:
            return

        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            self.camera.release()
            self.camera = None

            messagebox.showerror(
                "Camera Error",
                "Could not open the webcam.",
                parent=self.window,
            )
            return

        self.camera_running = True

        self.camera_button.config(
            state="disabled"
        )

        self.scan_button.config(
            state="normal"
        )

        self.status_label.config(
            text="Camera running. Look at the camera and press Scan Face."
        )

        self._camera_loop()

    def _camera_loop(self):
        if not self.camera_running:
            return

        if self.camera is None:
            return

        ok, frame = self.camera.read()

        if not ok:
            self.status_label.config(
                text="Could not read webcam frame."
            )

            self.stop_camera()
            return

        self.latest_frame = frame

        cv2.imshow(
            "Attendance Camera",
            frame,
        )

        cv2.waitKey(1)

        self.window.after(
            30,
            self._camera_loop,
        )

    def scan_face(self):
        if self.latest_frame is None:
            messagebox.showwarning(
                "Scan Face",
                "Start the camera first.",
                parent=self.window,
            )
            return

        if self.session_id is None:
            messagebox.showwarning(
                "Scan Face",
                "Start an attendance session first.",
                parent=self.window,
            )
            return

        self.scan_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="Recognizing face..."
        )

        self.window.update_idletasks()

        try:
            result = self.service.recognize_and_mark(
                self.latest_frame.copy(),
                self.session_id,
            )

            student_id = result.get(
                "student_id"
            )

            if result["status"] == "present":
                name = self.service.get_student_name(
                    student_id
                )

                self.status_label.config(
                    text=f"PRESENT: {name} (ID {student_id})"
                )

            elif result["status"] == "duplicate":
                name = self.service.get_student_name(
                    student_id
                )

                self.status_label.config(
                    text=f"ALREADY MARKED: {name}"
                )

            else:
                self.status_label.config(
                    text="UNKNOWN FACE: Attendance not marked."
                )

        except Exception as exc:
            messagebox.showerror(
                "Recognition Error",
                str(exc),
                parent=self.window,
            )

        finally:
            if self.camera_running:
                self.scan_button.config(
                    state="normal"
                )

    def stop_camera(self):
        self.camera_running = False

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        cv2.destroyAllWindows()

        if self.session_id is not None:
            self.camera_button.config(
                state="normal"
            )

            self.scan_button.config(
                state="disabled"
            )

    def close(self):
        self.stop_camera()
        self.window.destroy()

