from __future__ import annotations

import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2

from app.recognition.face_engine import FaceRecognitionEngine
from app.registration.service import RegistrationService


class RegistrationWindow:
    """Tkinter window for consented student face registration."""

    def __init__(self, parent: tk.Misc):
        self.parent = parent

        self.window = tk.Toplevel(parent)
        self.window.title("Student Registration")
        self.window.geometry("700x650")
        self.window.resizable(False, False)

        self.camera = None
        self.engine = FaceRecognitionEngine()

        self.capturing = False
        self.samples = []
        self.last_capture_time = 0.0

        self.roll_no_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.course_var = tk.StringVar()
        self.semester_var = tk.StringVar()
        self.section_var = tk.StringVar()
        self.consent_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(
            value="Enter student details and give consent."
        )
        self.sample_var = tk.StringVar(value="Samples: 0 / 5")

        self._build_ui()

        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        container = ttk.Frame(self.window, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Student Registration",
            font=("Arial", 20, "bold"),
        ).pack(pady=(0, 15))

        form = ttk.Frame(container)
        form.pack(fill="x")

        fields = [
            ("Roll Number", self.roll_no_var),
            ("Student Name", self.name_var),
            ("Course", self.course_var),
            ("Semester", self.semester_var),
            ("Section", self.section_var),
        ]

        for row, (label, variable) in enumerate(fields):
            ttk.Label(
                form,
                text=label + ":",
            ).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 10),
                pady=5,
            )

            ttk.Entry(
                form,
                textvariable=variable,
                width=45,
            ).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=5,
            )

        form.columnconfigure(1, weight=1)

        ttk.Checkbutton(
            container,
            text=(
                "I confirm that the student has given consent "
                "for biometric face registration."
            ),
            variable=self.consent_var,
        ).pack(
            anchor="w",
            pady=(15, 10),
        )

        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=10)

        ttk.Button(
            controls,
            text="Start Camera",
            command=self.start_camera,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            controls,
            text="Capture Sample",
            command=self.capture_sample,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            controls,
            text="Register Student",
            command=self.register_student,
        ).pack(side="left")

        ttk.Label(
            container,
            textvariable=self.sample_var,
            font=("Arial", 12, "bold"),
        ).pack(pady=5)

        ttk.Label(
            container,
            textvariable=self.status_var,
            wraplength=600,
        ).pack(pady=10)

        ttk.Label(
            container,
            text=(
                "Registration requires 5 valid samples. "
                "Keep exactly one face visible."
            ),
            wraplength=600,
        ).pack(pady=5)

        ttk.Button(
            container,
            text="Close",
            command=self.close,
        ).pack(pady=15)

    def start_camera(self):
        if not self.consent_var.get():
            messagebox.showwarning(
                "Consent Required",
                "Consent must be confirmed before starting face registration.",
                parent=self.window,
            )
            return

        if self.camera is not None:
            self.status_var.set("Camera is already running.")
            return

        self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.camera.isOpened():
            self.camera.release()
            self.camera = None

            messagebox.showerror(
                "Camera Error",
                "Could not open the webcam.",
                parent=self.window,
            )
            return

        self.capturing = True
        self.status_var.set(
            "Camera started. Keep exactly one face visible."
        )

        self._camera_loop()

    def _camera_loop(self):
        if not self.capturing or self.camera is None:
            return

        success, frame = self.camera.read()

        if not success:
            self.status_var.set(
                "Could not read a webcam frame."
            )
            self.window.after(30, self._camera_loop)
            return

        cv2.putText(
            frame,
            "Camera running - use Capture Sample",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        cv2.imshow(
            "Smart Attendance - Registration Camera",
            frame,
        )

        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            self.stop_camera()
            return

        self.window.after(30, self._camera_loop)

    def capture_sample(self):
        if not self.consent_var.get():
            messagebox.showwarning(
                "Consent Required",
                "Consent is required.",
                parent=self.window,
            )
            return

        if self.camera is None:
            messagebox.showwarning(
                "Camera Not Started",
                "Start the camera first.",
                parent=self.window,
            )
            return

        if len(self.samples) >= RegistrationService.REQUIRED_SAMPLES:
            self.status_var.set(
                "All required samples have already been captured."
            )
            return

        now = time.monotonic()

        if now - self.last_capture_time < 1.0:
            self.status_var.set(
                "Please wait briefly before capturing another sample."
            )
            return

        success, frame = self.camera.read()

        if not success:
            self.status_var.set(
                "Could not capture a webcam frame."
            )
            return

        try:
            analysis = self.engine.analyze_frame(frame)

            if analysis["face_count"] == 0:
                self.status_var.set(
                    "No face detected. Position your face clearly."
                )
                return

            if analysis["face_count"] > 1:
                self.status_var.set(
                    "Multiple faces detected. Only one person may be visible."
                )
                return

            embedding = analysis["embedding"]

            self.samples.append(embedding)
            self.last_capture_time = now

            count = len(self.samples)

            self.sample_var.set(
                f"Samples: {count} / "
                f"{RegistrationService.REQUIRED_SAMPLES}"
            )

            if count < RegistrationService.REQUIRED_SAMPLES:
                self.status_var.set(
                    "Sample captured successfully. "
                    "Change your head position slightly and capture again."
                )
            else:
                self.status_var.set(
                    "All 5 samples captured. "
                    "You can now register the student."
                )

        except Exception as exc:
            self.status_var.set(
                f"Could not capture sample: {type(exc).__name__}: {exc}"
            )

    def register_student(self):
        if not self.consent_var.get():
            messagebox.showwarning(
                "Consent Required",
                "Student consent is required.",
                parent=self.window,
            )
            return

        try:
            student_id = RegistrationService.register_student(
                roll_no=self.roll_no_var.get(),
                name=self.name_var.get(),
                course=self.course_var.get(),
                semester=self.semester_var.get(),
                section=self.section_var.get(),
                consent_given=True,
                embeddings=self.samples,
            )

        except ValueError as exc:
            messagebox.showwarning(
                "Registration Validation",
                str(exc),
                parent=self.window,
            )
            return

        except Exception as exc:
            messagebox.showerror(
                "Registration Error",
                f"Registration failed:\n{type(exc).__name__}: {exc}",
                parent=self.window,
            )
            return

        messagebox.showinfo(
            "Registration Successful",
            f"Student registered successfully.\nStudent ID: {student_id}",
            parent=self.window,
        )

        self.samples.clear()
        self.sample_var.set("Samples: 0 / 5")
        self.status_var.set("Registration completed successfully.")

    def stop_camera(self):
        self.capturing = False

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        cv2.destroyAllWindows()

    def close(self):
        self.stop_camera()
        self.window.destroy()
