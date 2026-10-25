from app.database.db import get_connection

def add_student(roll_no, name, course=None, semester=None, section=None):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO students (roll_no, name, course, semester, section) VALUES (?, ?, ?, ?, ?)",
            (roll_no, name, course, semester, section),
        )
        conn.commit()
        return cur.lastrowid

def get_active_students():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM students WHERE status = 'active' ORDER BY roll_no"
        ).fetchall()

def create_subject(code, name, semester=None):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO subjects (code, name, semester) VALUES (?, ?, ?)",
            (code, name, semester),
        )
        conn.commit()
        return cur.lastrowid

def create_session(subject_id, date, start_time, end_time=None):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (subject_id, date, start_time, end_time) VALUES (?, ?, ?, ?)",
            (subject_id, date, start_time, end_time),
        )
        conn.commit()
        return cur.lastrowid

def mark_attendance(student_id, session_id, status="present", confidence=None):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO attendance
               (student_id, session_id, status, confidence)
               VALUES (?, ?, ?, ?)""",
            (student_id, session_id, status, confidence),
        )
        conn.commit()
        return cur.rowcount


def add_face_embedding(student_id, embedding, sample_number):
    """Store one normalized face embedding for a student."""
    import numpy as np

    vector = np.asarray(embedding, dtype=np.float32).reshape(-1)

    if vector.size != 512:
        raise ValueError(
            f"Expected a 512-dimensional embedding, got {vector.size}."
        )

    norm = float(np.linalg.norm(vector))

    if norm == 0.0:
        raise ValueError("Cannot store a zero-magnitude embedding.")

    vector = vector / norm

    data = vector.tobytes()

    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO face_data
               (student_id, embedding, sample_number)
               VALUES (?, ?, ?)""",
            (student_id, data, int(sample_number)),
        )
        conn.commit()
        return cur.lastrowid


def get_student_embeddings(student_id):
    """Return all stored embeddings for one student."""
    import numpy as np

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT face_id, student_id, embedding, sample_number
               FROM face_data
               WHERE student_id = ?
               ORDER BY sample_number""",
            (student_id,),
        ).fetchall()

    embeddings = []

    for row in rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)

        if vector.size != 512:
            continue

        embeddings.append(
            {
                "face_id": row["face_id"],
                "student_id": row["student_id"],
                "sample_number": row["sample_number"],
                "embedding": vector.copy(),
            }
        )

    return embeddings


def get_all_student_embeddings():
    """Return all registered student embeddings for recognition."""
    import numpy as np

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT student_id, embedding, sample_number
               FROM face_data
               ORDER BY student_id, sample_number"""
        ).fetchall()

    results = []

    for row in rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)

        if vector.size != 512:
            continue

        results.append(
            (
                row["student_id"],
                vector.copy(),
            )
        )

    return results
