from __future__ import annotations

import calendar
from datetime import date

from app.database.db import get_connection


class AttendanceCalendarService:
    """Read-only, student-scoped attendance calendar queries."""

    def get_subjects(self, student_id: int) -> list[dict]:
        """Return subjects that have sessions for this student."""
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT
                    sub.subject_id,
                    sub.code,
                    sub.name,
                    sub.semester
                FROM subjects AS sub
                JOIN sessions AS ses
                    ON ses.subject_id = sub.subject_id
                WHERE EXISTS (
                    SELECT 1
                    FROM attendance AS a
                    WHERE a.student_id = ?
                      AND a.session_id = ses.session_id
                )
                ORDER BY sub.code
                """,
                (student_id,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_month_calendar(
        self,
        student_id: int,
        year: int,
        month: int,
        subject_id: int | None = None,
    ) -> dict:
        """
        Return scheduled sessions and recorded attendance for one month.

        Missing attendance is reported as 'not_recorded', not 'absent',
        because this project does not currently confirm absences.
        """
        if not isinstance(year, int) or not 1 <= year <= 9999:
            raise ValueError("Year must be between 1 and 9999.")

        if not isinstance(month, int) or not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12.")

        _, days_in_month = calendar.monthrange(year, month)
        start_date = date(year, month, 1).isoformat()
        end_date = date(year, month, days_in_month).isoformat()

        query = """
            SELECT
                ses.session_id,
                ses.date,
                ses.start_time,
                ses.end_time,
                sub.subject_id,
                sub.code AS subject_code,
                sub.name AS subject_name,
                a.status AS attendance_status,
                a.marked_at
            FROM sessions AS ses
            JOIN subjects AS sub
                ON sub.subject_id = ses.subject_id
            LEFT JOIN attendance AS a
                ON a.session_id = ses.session_id
               AND a.student_id = ?
            WHERE ses.date >= ?
              AND ses.date <= ?
        """

        params: list = [student_id, start_date, end_date]

        if subject_id is not None:
            query += " AND sub.subject_id = ?"
            params.append(subject_id)

        query += " ORDER BY ses.date, ses.start_time, sub.code"

        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        sessions_by_date: dict[str, list[dict]] = {}

        for row in rows:
            item = dict(row)

            status = item.pop("attendance_status")
            item["status"] = (
                status.lower()
                if status is not None
                else "not_recorded"
            )

            item["marked_at"] = item["marked_at"]

            sessions_by_date.setdefault(item["date"], []).append(item)

        return {
            "student_id": student_id,
            "year": year,
            "month": month,
            "days_in_month": days_in_month,
            "sessions_by_date": sessions_by_date,
        }

    def get_subject_summaries(self, student_id: int) -> list[dict]:
        """
        Summarize each subject using scheduled sessions as the denominator.

        Percentage is based on sessions with recorded 'present' status.
        Missing attendance records are counted separately and are not
        automatically classified as confirmed absences.
        """
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    sub.subject_id,
                    sub.code AS subject_code,
                    sub.name AS subject_name,
                    COUNT(ses.session_id) AS scheduled_sessions,
                    SUM(
                        CASE
                            WHEN LOWER(COALESCE(a.status, '')) = 'present'
                            THEN 1 ELSE 0
                        END
                    ) AS present_sessions,
                    SUM(
                        CASE
                            WHEN a.attendance_id IS NULL
                            THEN 1 ELSE 0
                        END
                    ) AS unrecorded_sessions
                FROM subjects AS sub
                JOIN sessions AS ses
                    ON ses.subject_id = sub.subject_id
                LEFT JOIN attendance AS a
                    ON a.session_id = ses.session_id
                   AND a.student_id = ?
                GROUP BY
                    sub.subject_id,
                    sub.code,
                    sub.name
                ORDER BY sub.code
                """,
                (student_id,),
            ).fetchall()

        summaries = []

        for row in rows:
            scheduled = row["scheduled_sessions"] or 0
            present = row["present_sessions"] or 0
            unrecorded = row["unrecorded_sessions"] or 0

            percentage = (
                round(present / scheduled * 100.0, 2)
                if scheduled > 0
                else 0.0
            )

            summaries.append(
                {
                    "subject_id": row["subject_id"],
                    "subject_code": row["subject_code"],
                    "subject_name": row["subject_name"],
                    "scheduled_sessions": scheduled,
                    "present_sessions": present,
                    "unrecorded_sessions": unrecorded,
                    "percentage": percentage,
                    "below_75_percent": percentage < 75.0,
                }
            )

        return summaries