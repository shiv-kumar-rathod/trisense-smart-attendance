from __future__ import annotations

from typing import Any

import numpy as np
from insightface.app import FaceAnalysis


class FaceRecognitionEngine:
    def __init__(
        self,
        tolerance: float = 0.50,
        model_name: str = "buffalo_l",
        det_size: tuple[int, int] = (640, 640),
    ):
        self.tolerance = float(tolerance)
        self.model_name = model_name
        self.det_size = det_size
        self._app: FaceAnalysis | None = None
        self._known_embeddings: list[np.ndarray] = []
        self._known_student_ids: list[int] = []

    def initialize(self) -> None:
        if self._app is not None:
            return

        self._app = FaceAnalysis(
            name=self.model_name,
            providers=["CPUExecutionProvider"],
        )
        self._app.prepare(ctx_id=0, det_size=self.det_size)

    def detect_faces(self, frame: np.ndarray) -> list[Any]:
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("frame must be a valid OpenCV image.")

        if frame.size == 0:
            raise ValueError("frame is empty.")

        self.initialize()
        return list(self._app.get(frame))

    @staticmethod
    def _extract_embedding(face: Any) -> np.ndarray:
        embedding = getattr(face, "embedding", None)

        if embedding is None:
            raise ValueError("InsightFace did not return a face embedding.")

        embedding = np.asarray(embedding, dtype=np.float32).reshape(-1)

        if embedding.size == 0:
            raise ValueError("Face embedding is empty.")

        norm = float(np.linalg.norm(embedding))

        if norm == 0.0:
            raise ValueError("Face embedding has zero magnitude.")

        return embedding / norm

    def get_embedding(self, frame: np.ndarray) -> np.ndarray | None:
        faces = self.detect_faces(frame)

        if len(faces) == 0:
            return None

        if len(faces) > 1:
            raise ValueError(
                f"Expected exactly one face, but detected {len(faces)} faces."
            )

        return self._extract_embedding(faces[0])

    def analyze_frame(self, frame: np.ndarray) -> dict[str, Any]:
        faces = self.detect_faces(frame)

        result = {
            "face_count": len(faces),
            "faces": faces,
            "embedding": None,
            "status": "no_face",
        }

        if len(faces) == 1:
            result["embedding"] = self._extract_embedding(faces[0])
            result["status"] = "one_face"
        elif len(faces) > 1:
            result["status"] = "multiple_faces"

        return result

    def load_known_faces(
        self,
        student_embeddings: list[tuple[int, np.ndarray]],
    ) -> None:
        self._known_student_ids = []
        self._known_embeddings = []

        for student_id, embedding in student_embeddings:
            normalized = np.asarray(
                embedding,
                dtype=np.float32,
            ).reshape(-1)

            norm = float(np.linalg.norm(normalized))

            if norm == 0.0:
                continue

            self._known_student_ids.append(int(student_id))
            self._known_embeddings.append(normalized / norm)

    def recognize_embedding(
        self,
        embedding: np.ndarray,
    ) -> dict[str, Any] | None:
        if not self._known_embeddings:
            return None

        query = np.asarray(
            embedding,
            dtype=np.float32,
        ).reshape(-1)

        norm = float(np.linalg.norm(query))

        if norm == 0.0:
            return None

        query = query / norm

        best_student_id = None
        best_distance = float("inf")

        for student_id, known in zip(
            self._known_student_ids,
            self._known_embeddings,
        ):
            if known.shape != query.shape:
                continue

            distance = float(np.linalg.norm(query - known))

            if distance < best_distance:
                best_distance = distance
                best_student_id = student_id

        if best_student_id is None or best_distance > self.tolerance:
            return {
                "student_id": None,
                "distance": best_distance,
                "matched": False,
            }

        return {
            "student_id": best_student_id,
            "distance": best_distance,
            "matched": True,
        }

    def recognize_frame(self, frame: np.ndarray) -> dict[str, Any]:
        analysis = self.analyze_frame(frame)

        if analysis["status"] == "no_face":
            return {
                "status": "no_face",
                "student_id": None,
                "distance": None,
                "matched": False,
            }

        if analysis["status"] == "multiple_faces":
            return {
                "status": "multiple_faces",
                "student_id": None,
                "distance": None,
                "matched": False,
            }

        result = self.recognize_embedding(analysis["embedding"])

        if result is None:
            return {
                "status": "no_known_faces",
                "student_id": None,
                "distance": None,
                "matched": False,
            }

        result["status"] = "recognized" if result["matched"] else "unknown"
        return result
