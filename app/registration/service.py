from __future__ import annotations

from typing import Iterable

import numpy as np

from app.database.db import get_connection


class RegistrationService:
    """Business logic for student registration and face samples."""

    REQUIRED_SAMPLES = 5
    EMBEDDING_DIMENSION = 512

    @staticmethod
    def validate_student_details(
        roll_no: str,
        name: str,
        course: str | None = None,
        semester: str | None = None,
        section: str | None = None,
    ) -> None:
        roll_no = (roll_no or "").strip()
        name = (name or "").strip()

        if not roll_no:
            raise ValueError("Roll number is required.")

        if not name:
            raise ValueError("Student name is required.")

        if len(roll_no) > 50:
            raise ValueError("Roll number is too long.")

        if len(name) > 150:
            raise ValueError("Student name is too long.")

    @classmethod
    def validate_embeddings(
        cls,
        embeddings: Iterable[np.ndarray],
    ) -> list[np.ndarray]:
        validated = []

        for embedding in embeddings:
            vector = np.asarray(
                embedding,
                dtype=np.float32,
            ).reshape(-1)

            if vector.size != cls.EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Every face embedding must contain exactly "
                    f"{cls.EMBEDDING_DIMENSION} values."
                )

            norm = float(np.linalg.norm(vector))

            if norm == 0.0:
                raise ValueError(
                    "A face embedding has zero magnitude."
                )

            validated.append(vector / norm)

        if len(validated) < cls.REQUIRED_SAMPLES:
            raise ValueError(
                f"At least {cls.REQUIRED_SAMPLES} face samples "
                "are required."
            )

        return validated

    @classmethod
    def register_student(
        cls,
        *,
        roll_no: str,
        name: str,
        course: str | None,
        semester: str | None,
        section: str | None,
        consent_given: bool,
        embeddings: Iterable[np.ndarray],
    ) -> int:

        if not consent_given:
            raise ValueError(
                "Student consent is required before face registration."
            )

        cls.validate_student_details(
            roll_no,
            name,
            course,
            semester,
            section,
        )

        validated_embeddings = cls.validate_embeddings(embeddings)

        with get_connection() as conn:
            try:
                existing = conn.execute(
                    "SELECT student_id FROM students WHERE roll_no = ?",
                    (roll_no.strip(),),
                ).fetchone()

                if existing is not None:
                    raise ValueError(
                        f"Roll number '{roll_no.strip()}' "
                        "is already registered."
                    )

                cursor = conn.execute(
                    """
                    INSERT INTO students
                    (roll_no, name, course, semester, section)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        roll_no.strip(),
                        name.strip(),
                        course.strip() if course else None,
                        semester.strip() if semester else None,
                        section.strip() if section else None,
                    ),
                )

                student_id = cursor.lastrowid

                if student_id is None:
                    raise RuntimeError(
                        "Student record was not created."
                    )

                for sample_number, embedding in enumerate(
                    validated_embeddings,
                    start=1,
                ):
                    conn.execute(
                        """
                        INSERT INTO face_data
                        (student_id, embedding, sample_number)
                        VALUES (?, ?, ?)
                        """,
                        (
                            student_id,
                            embedding.tobytes(),
                            sample_number,
                        ),
                    )

                conn.commit()
                return int(student_id)

            except Exception:
                conn.rollback()
                raise
