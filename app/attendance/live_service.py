from __future__ import annotations

from datetime import datetime

import numpy as np

from app.attendance.service import AttendanceService
from app.database.db import get_connection
from app.database.repositories import mark_attendance
from app.recognition.service import RecognitionService


class LiveAttendanceService:
    def __init__(self, tolerance: float = 0.65):
        self.recognition = RecognitionService(
            tolerance=tolerance
        )
        self.attendance = AttendanceService()

    def load_registered_faces(self) -> int:
        return self.recognition.load_registered_faces()

    def recognize_and_mark(
        self,
        frame: np.ndarray,
        session_id: int,
    ) -> dict:
        result = self.recognition.recognize_frame(frame)

        if not result.get("matched"):
            return {
                "success": False,
                "status": "unknown",
                "student_id": None,
                "distance": result.get("distance"),
                "message": "Unknown face.",
            }

        student_id = result["student_id"]
        distance = result.get("distance")

        inserted = self.attendance.mark_present(
            student_id,
            session_id,
            distance,
        )

        if inserted:
            return {
                "success": True,
                "status": "present",
                "student_id": student_id,
                "distance": distance,
                "message": "Attendance marked successfully.",
            }

        return {
            "success": False,
            "status": "duplicate",
            "student_id": student_id,
            "distance": distance,
            "message": "Attendance already marked for this session.",
        }

    def get_student_name(self, student_id: int) -> str:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT name
                FROM students
                WHERE student_id = ?
                """,
                (student_id,),
            ).fetchone()

        if row is None:
            return "Unknown student"

        return row["name"]


