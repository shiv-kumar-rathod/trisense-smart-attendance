from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_FACES_DIR = DATA_DIR / "raw_faces"
ENCODINGS_DIR = DATA_DIR / "encodings"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "attendance.db"
LOG_DIR = BASE_DIR / "logs"

APP_NAME = "TRISENSE"

# Confirm these against the college policy before final deployment.
ATTENDANCE_GOOD_THRESHOLD = 85.0
ATTENDANCE_WARNING_THRESHOLD = 75.0

FACE_MATCH_TOLERANCE = 0.50
CAMERA_INDEX = 0
