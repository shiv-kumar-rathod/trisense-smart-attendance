from __future__ import annotations

from datetime import datetime

from app.database.db import get_connection
from app.database.repositories import create_session, create_subject


class AttendanceSessionService:
    """Create and retrieve subject attendance sessions."""

    @staticmethod
    def create_subject(code: str, name: str, semester: str | None = None) -> int:
        code = (code or "").strip()
        name = (name or "").strip()

        if not code:
            raise ValueError("Subject code is required.")

        if not name:
            raise ValueError("Subject name is required.")

        return create_subject(code, name, semester)

    @staticmethod
    def create_session(
        subject_id: int,
        date: str,
        start_time: str,
        end_time: str | None = None,
    ) -> int:
        if not subject_id:
            raise ValueError("Subject ID is required.")

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Date must use YYYY-MM-DD format.") from exc

        try:
            datetime.strptime(start_time, "%H:%M:%S")
        except ValueError as exc:
            raise ValueError("Start time must use HH:MM:SS format.") from exc

        if end_time:
            try:
                datetime.strptime(end_time, "%H:%M:%S")
            except ValueError as exc:
                raise ValueError("End time must use HH:MM:SS format.") from exc

        return create_session(
            subject_id,
            date,
            start_time,
            end_time,
        )

    @staticmethod
    def get_session(session_id: int):
        with get_connection() as conn:
            return conn.execute(
                """
                SELECT
                    s.session_id,
                    s.subject_id,
                    s.date,
                    s.start_time,
                    s.end_time,
                    sub.code AS subject_code,
                    sub.name AS subject_name
                FROM sessions s
                JOIN subjects sub
                    ON sub.subject_id = s.subject_id
                WHERE s.session_id = ?
                """,
                (session_id,),
            ).fetchone()
