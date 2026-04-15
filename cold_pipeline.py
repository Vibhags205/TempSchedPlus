from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import os
import shutil
import time

import config
import prediction


MANIFEST_PATH = config.LOGS / "cold_pipeline_manifest.json"


def _scan_paths_from_config():
    default_paths = [Path.home() / "Documents", Path.home() / "Downloads"]
    return getattr(config, "SCAN_PATHS", default_paths)


def _scan_max_files_from_config():
    return int(getattr(config, "SCAN_MAX_FILES", 1500))


def _scan_min_size_from_config():
    return int(getattr(config, "SCAN_MIN_SIZE_BYTES", 4096))


def _skip_extensions_from_config():
    return set(getattr(config, "SKIP_EXTENSIONS", {".exe", ".dll", ".sys"}))


def should_skip(file_path: Path):
    return file_path.suffix.lower() in _skip_extensions_from_config()


def _safe_stat(file_path: Path):
    try:
        return file_path.stat()
    except (PermissionError, FileNotFoundError, OSError):
        return None


def _load_manifest():
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return []


def _save_manifest(records):
    MANIFEST_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


def _device_stage_path(source_path: Path):
    source_hash = str(abs(hash(str(source_path.resolve()))))
    return config.DEVICE / f"stage_{source_hash}_{source_path.name}"


def _edge_stage_path(source_path: Path):
    source_hash = str(abs(hash(str(source_path.resolve()))))
    return config.EDGE / f"stage_{source_hash}_{source_path.name}"


def _cloud_stage_pattern(source_path: Path):
    source_hash = str(abs(hash(str(source_path.resolve()))))
    return f"stage_{source_hash}_{source_path.stem}.bundle.enc"


def _is_present_in_any_tier(source_path: Path):
    if _device_stage_path(source_path).exists():
        return True
    if _edge_stage_path(source_path).exists():
        return True
    if (config.CLOUD / _cloud_stage_pattern(source_path)).exists():
        return True
    return False


def stage_to_device(source_path: Path):
    staged_path = _device_stage_path(source_path)
    staged_path.parent.mkdir(parents=True, exist_ok=True)
    if not staged_path.exists():
        shutil.copy2(source_path, staged_path)
    return staged_path


def get_files(scan_paths=None, max_files=None):
    selected_paths = scan_paths or _scan_paths_from_config()
    limit = max_files or _scan_max_files_from_config()

    file_data = []
    for root_path in selected_paths:
        root = Path(root_path)
        if not root.exists() or not root.is_dir():
            continue

        for current_root, _, files in os.walk(root):
            for filename in files:
                path = Path(current_root) / filename
                if should_skip(path):
                    continue

                stats = _safe_stat(path)
                if stats is None:
                    continue
                if stats.st_size < _scan_min_size_from_config():
                    continue

                file_data.append(
                    {
                        "path": str(path),
                        "size": int(stats.st_size),
                        "last_access": float(stats.st_atime),
                        "last_modified": float(stats.st_mtime),
                    }
                )

                if len(file_data) >= limit:
                    return file_data

    return file_data


def classify_file(file_info):
    current_time = time.time()
    last_access_days = (current_time - float(file_info["last_access"])) / (60 * 60 * 24)

    if last_access_days < 2:
        return "hot"
    if last_access_days < 7:
        return "warm"
    return "cold"


def classify_with_ai(file_info):
    raw_pred = prediction.predict(file_info)
    normalized = min(max(raw_pred / 800.0, 0.0), 1.0)
    if normalized > 0.7:
        return "hot", raw_pred
    return "cold", raw_pred


def final_decision(file_info):
    rule_decision = classify_file(file_info)
    ai_decision, raw_prediction = classify_with_ai(file_info)

    if rule_decision == "cold" and ai_decision == "cold":
        decision = "cold"
    elif rule_decision == "hot" or ai_decision == "hot":
        decision = "hot"
    else:
        decision = "warm"

    return decision, rule_decision, ai_decision, raw_prediction


def process_files(scan_paths=None, max_files=None):
    records = _load_manifest()
    processed_paths = {entry.get("original_path") for entry in records}

    files = get_files(scan_paths=scan_paths, max_files=max_files)
    cycle = {
        "scanned": len(files),
        "hot": 0,
        "warm": 0,
        "cold": 0,
        "staged": 0,
        "entries": [],
        "classified": [],
        "hot_files": [],
    }

    for file_info in files:
        decision, rule_decision, ai_decision, raw_prediction = final_decision(file_info)
        cycle[decision] += 1

        path = Path(file_info["path"])
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "original_path": str(path),
            "size": file_info["size"],
            "decision": decision,
            "rule_decision": rule_decision,
            "ai_decision": ai_decision,
            "predicted_temperature": raw_prediction,
        }

        cycle["classified"].append(
            {
                "path": str(path),
                "size": file_info["size"],
                "decision": decision,
                "rule_decision": rule_decision,
                "ai_decision": ai_decision,
                "predicted_temperature": raw_prediction,
            }
        )
        if decision == "hot":
            cycle["hot_files"].append(str(path))

        should_stage = str(path) not in processed_paths or not _is_present_in_any_tier(path)
        if should_stage:
            try:
                staged_path = stage_to_device(path)
            except (FileNotFoundError, PermissionError, OSError):
                continue

            entry.update(
                {
                    "staged_path": str(staged_path),
                    "staged_tier": "device",
                }
            )
            records.append(entry)
            processed_paths.add(str(path))

            cycle["staged"] += 1
            cycle["entries"].append(entry)

    _save_manifest(records)

    # Keep payload bounded for UI/session storage.
    cycle["classified"] = cycle["classified"][:200]
    cycle["hot_files"] = cycle["hot_files"][:50]
    return cycle


def get_pipeline_stats():
    records = _load_manifest()
    total_staged = sum(int(item.get("size", 0)) for item in records)
    return {
        "compressed_records": len(records),
        "saved_bytes": total_staged,
        "saved_mb": round(total_staged / (1024 * 1024), 2),
        "recent": records[-10:],
    }