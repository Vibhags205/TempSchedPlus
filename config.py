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

SCAN_DEFAULT_PATHS = [Path.home() / "Documents", Path.home() / "Downloads"]
SCAN_PATHS_ENV = os.getenv("TEMPSCHED_SCAN_PATHS", "")
SCAN_PATHS = [Path(part.strip()) for part in SCAN_PATHS_ENV.split(";") if part.strip()] or SCAN_DEFAULT_PATHS
SCAN_MAX_FILES = int(os.getenv("TEMPSCHED_SCAN_MAX_FILES", "1500"))
SCAN_MIN_SIZE_BYTES = int(os.getenv("TEMPSCHED_SCAN_MIN_SIZE_BYTES", "4096"))

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
