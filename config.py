import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DEVICE = BASE_DIR / "device"
EDGE = BASE_DIR / "edge"
CLOUD = BASE_DIR / "cloud"
COMPRESSED = BASE_DIR / "compressed"
ENCRYPTED = BASE_DIR / "encrypted"
LOGS = BASE_DIR / "logs"
MODELS = BASE_DIR / "models"

HOT_THRESHOLD = 600
WARM_THRESHOLD = 400

# Newton-style hotness cooling parameters.
TEMP_AMBIENT = float(os.getenv("TEMPSCHED_TEMP_AMBIENT", "350.0"))
TEMP_DECAY_RATE_PER_HOUR = float(os.getenv("TEMPSCHED_TEMP_DECAY_RATE_PER_HOUR", "0.25"))

SCAN_DEFAULT_PATHS = [Path.home() / "Documents", Path.home() / "Downloads"]
SCAN_PATHS_ENV = os.getenv("TEMPSCHED_SCAN_PATHS", "")
SCAN_PATHS = [Path(part.strip()) for part in SCAN_PATHS_ENV.split(";") if part.strip()] or SCAN_DEFAULT_PATHS
SCAN_MAX_FILES = int(os.getenv("TEMPSCHED_SCAN_MAX_FILES", "1500"))
SCAN_MIN_SIZE_BYTES = int(os.getenv("TEMPSCHED_SCAN_MIN_SIZE_BYTES", "4096"))

FIREBASE_KEY_FILE = os.getenv("FIREBASE_KEY_FILE", "firebase_key.json")
FIREBASE_KEY_PATH = Path(FIREBASE_KEY_FILE) if Path(FIREBASE_KEY_FILE).is_absolute() else BASE_DIR / FIREBASE_KEY_FILE
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")
FIREBASE_METADATA_COLLECTION = os.getenv("FIREBASE_METADATA_COLLECTION", "files")

ENABLE_UPLOAD_ENCRYPTION = os.getenv("TEMPSCHED_ENABLE_UPLOAD_ENCRYPTION", "1").strip().lower() in {"1", "true", "yes", "on"}
DELETE_AFTER_UPLOAD = os.getenv("TEMPSCHED_DELETE_AFTER_UPLOAD", "0").strip().lower() in {"1", "true", "yes", "on"}

SKIP_EXTENSIONS = {
	".exe",
	".dll",
	".sys",
	".msi",
	".bat",
	".cmd",
	".ps1",
	".lnk",
}

ALL_DIRECTORIES = [DEVICE, EDGE, CLOUD, COMPRESSED, ENCRYPTED, LOGS, MODELS]


def ensure_directories():
	for directory in ALL_DIRECTORIES:
		directory.mkdir(parents=True, exist_ok=True)


ensure_directories()
