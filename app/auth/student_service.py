
from __future__ import annotations

import sqlite3

from app.auth.password_utils import hash_password, verify_password
from app.database.db import get_connection


class StudentAuthenticationService:
    """Create and authenticate accounts linked to registered students."""

    def create_student_account(
        self,
        student_id: int,
        username: str,
        password: str,
    ) -> int:
        username = username.strip()

        if not username:
            raise ValueError("Username must not be empty.")

        if len(username) > 100:
            raise ValueError("Username cannot exceed 100 characters.")

        if len(password) < 12:
            raise ValueError("Password must contain at least 12 characters.")

        password_hash = hash_password(password)

        with get_connection() as conn:
            try:
                student = conn.execute(
                    """
                    SELECT student_id, status
                    FROM students
                    WHERE student_id = ?
                    """,
                    (student_id,),
                ).fetchone()

                if student is None:
                    raise ValueError("The selected student does not exist.")

                if student["status"] != "active":
                    raise ValueError("Only active students can have login accounts.")

                cursor = conn.execute(
                    """
                    INSERT INTO student_accounts
                        (student_id, username, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (student_id, username, password_hash),
                )

                conn.commit()
                return int(cursor.lastrowid)

            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise ValueError(
                    "This username is already used, or this student already "
                    "has a login account."
                ) from exc

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> dict | None:
        username = username.strip()

        if not username or not password:
            return None

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    sa.account_id,
                    sa.username,
                    sa.student_id,
                    s.roll_no,
                    s.name,
                    s.course,
                    s.semester,
                    s.section,
                    s.status,
                    sa.password_hash
                FROM student_accounts AS sa
                JOIN students AS s
                    ON s.student_id = sa.student_id
                WHERE sa.username = ?
                """,
                (username,),
            ).fetchone()

            if row is None:
                return None

            if row["status"] != "active":
                return None

            if not verify_password(password, row["password_hash"]):
                return None

            return {
                "account_id": row["account_id"],
                "username": row["username"],
                "role": "student",
                "student_id": row["student_id"],
                "roll_no": row["roll_no"],
                "name": row["name"],
                "course": row["course"],
                "semester": row["semester"],
                "section": row["section"],
            }
