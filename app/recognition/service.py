from __future__ import annotations

from typing import Any

import numpy as np

from app.database.repositories import get_all_student_embeddings
from app.recognition.face_engine import FaceRecognitionEngine


class RecognitionService:
    """Load registered faces and recognize live face embeddings."""

    def __init__(self, tolerance: float = 0.65):
        self.engine = FaceRecognitionEngine(tolerance=tolerance)
        self._loaded = False

    def load_registered_faces(self) -> int:
        records = get_all_student_embeddings()
        self.engine.load_known_faces(records)
        self._loaded = True
        return len(records)

    @property
    def registered_embedding_count(self) -> int:
        return len(self.engine._known_embeddings)

    def recognize_embedding(self, embedding: np.ndarray) -> dict[str, Any]:
        if not self._loaded:
            self.load_registered_faces()

        result = self.engine.recognize_embedding(embedding)

        if result is None:
            return {
                "matched": False,
                "student_id": None,
                "distance": None,
                "status": "no_registered_faces",
            }

        result["status"] = "recognized" if result["matched"] else "unknown"
        return result

    def recognize_frame(self, frame: np.ndarray) -> dict[str, Any]:
        if not self._loaded:
            self.load_registered_faces()

        return self.engine.recognize_frame(frame)

