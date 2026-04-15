from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import shutil

import compression
import config
import encryption
import firebase_backend


INDEX_PATH = config.CLOUD / "index.json"
LOG_PATH = config.LOGS / "actions.jsonl"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _load_index():
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return []


def _save_index(records):
    INDEX_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def log_event(action: str, filename: str, source_tier: str, target_tier: str, temp: float, details: dict | None = None):
    entry = {
        "timestamp": _now_iso(),
        "action": action,
        "filename": filename,
        "source_tier": source_tier,
        "target_tier": target_tier,
        "temperature": round(float(temp), 2),
        "details": details or {},
    }
    with LOG_PATH.open("a", encoding="utf-8") as file_handle:
        file_handle.write(json.dumps(entry) + "\n")


def move_to_edge(source_path: Path, temperature: float):
    destination = config.EDGE / source_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(destination))
    log_event("tier_move", source_path.name, "device", "edge", temperature, {"path": str(destination)})
    return destination


def archive_cold_file(source_path: Path, temperature: float):
    source_path = Path(source_path)
    compressed_path = compression.compress_file(source_path, config.COMPRESSED / f"{source_path.name}.gz")
    encrypted_path = encryption.encrypt_file(compressed_path, config.ENCRYPTED / f"{source_path.stem}.enc")

    cloud_name = f"{source_path.stem}.bundle.enc"
    cloud_path = config.CLOUD / cloud_name
    shutil.copy2(encrypted_path, cloud_path)

    firebase_object = None
    try:
        firebase_object = firebase_backend.upload_to_cloud(encrypted_path)
    except (FileNotFoundError, PermissionError, OSError, ValueError):
        firebase_object = None

    checksum = sha256(cloud_path.read_bytes()).hexdigest()
    records = _load_index()
    record = {
        "filename": source_path.name,
        "cloud_object": cloud_name,
        "firebase_object": firebase_object,
        "compressed_path": str(compressed_path),
        "encrypted_path": str(encrypted_path),
        "checksum": checksum,
        "size_bytes": cloud_path.stat().st_size,
        "stored_at": _now_iso(),
        "temperature": round(float(temperature), 2),
    }
    records = [item for item in records if item.get("filename") != source_path.name]
    records.append(record)
    _save_index(records)

    source_path.unlink(missing_ok=True)
    log_event("cold_archive", source_path.name, "device", "cloud", temperature, {"cloud_object": cloud_name})
    return record


def get_cloud_records():
    return _load_index()