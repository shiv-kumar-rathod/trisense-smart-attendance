from __future__ import annotations

import sqlite3

from app.database.db import get_connection
from app.auth.password_utils import hash_password, verify_password


ALLOWED_ROLES = {"admin", "reviewer"}


class AuthenticationService:
    """Register users and authenticate their credentials."""

    def create_user(
        self,
        username: str,
        password: str,
        role: str = "reviewer",
    ) -> int:
        username = username.strip()
        role = role.strip().lower()

        if not username:
            raise ValueError("Username must not be empty.")

        if len(username) > 100:
            raise ValueError("Username cannot exceed 100 characters.")

        if len(password) < 12:
            raise ValueError("Password must contain at least 12 characters.")

        if role not in ALLOWED_ROLES:
            raise ValueError("Role must be admin or reviewer.")

        password_hash = hash_password(password)
        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                """,
                (username, password_hash, role),
            )
            connection.commit()
            return int(cursor.lastrowid)

        except sqlite3.IntegrityError as exc:
            connection.rollback()
            raise ValueError(
                "That username already exists or violates a database constraint."
            ) from exc

        finally:
            connection.close()

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> dict | None:
        username = username.strip()

        if not username or not password:
            return None

        connection = get_connection()

        try:
            row = connection.execute(
                """
                SELECT user_id, username, password_hash, role
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

            if row is None:
                return None

            if not verify_password(password, row["password_hash"]):
                return None

            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "role": row["role"],
            }

        finally:
            connection.close()
