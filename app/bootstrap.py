from config import DATA_DIR, RAW_FACES_DIR, ENCODINGS_DIR, REPORTS_DIR, LOG_DIR
from app.database.db import initialize_database

def initialize_application():
    for directory in (DATA_DIR, RAW_FACES_DIR, ENCODINGS_DIR, REPORTS_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    initialize_database()
