import os

class Config:
    # --- Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    # --- MySQL ---
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "your_mysql_password")
    MYSQL_DB = os.environ.get("MYSQL_DB", "smart_attendance")

    # --- Face recognition ---
    ENCODINGS_FILE = os.path.join(os.path.dirname(__file__), "encodings", "encodings.pickle")
    FACE_TOLERANCE = 0.5          # lower = stricter match
    CAMERA_INDEX = 0              # default webcam

    # --- Excel export ---
    EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), "exports")
