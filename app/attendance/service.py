from __future__ import annotations

from app.database.db import get_connection
from app.database.repositories import mark_attendance


class AttendanceService:
    def mark_present(self, student_id, session_id, confidence=None):
        return mark_attendance(
            student_id,
            session_id,
            "present",
            confidence,
        )

    def calculate_percentage(self, present_sessions, total_sessions):
        if total_sessions <= 0:
            return 0.0

        return round(
            (present_sessions / total_sessions) * 100.0,
            2,
        )

    def get_student_attendance(self, student_id):
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_sessions,
                    SUM(
                        CASE
                            WHEN status = 'present' THEN 1
                            ELSE 0
                        END
                    ) AS present_sessions
                FROM attendance
                WHERE student_id = ?
                """,
                (student_id,),
            ).fetchone()

        total = row["total_sessions"] or 0
        present = row["present_sessions"] or 0

        percentage = self.calculate_percentage(
            present,
            total,
        )

        return {
            "student_id": student_id,
            "total_sessions": total,
            "present_sessions": present,
            "absent_sessions": total - present,
            "percentage": percentage,
        }

    def get_status(self, percentage, warning_threshold=75.0):
        if percentage >= 85.0:
            return "good"

        if percentage >= warning_threshold:
            return "warning"

        return "low"
