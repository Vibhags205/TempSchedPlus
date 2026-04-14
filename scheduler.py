from datetime import datetime, timezone
from pathlib import Path

import cloud_storage
import config
from temperature import calculate_temperature


temperature_store = {}


def _last_access_timestamp(path: Path) -> float:
    metadata = path.stat()
    return metadata.st_mtime if metadata.st_mtime else datetime.now(timezone.utc).timestamp()


def classify_temperature(temp: float):
    if temp >= config.HOT_THRESHOLD:
        return "HOT"
    if temp >= config.WARM_THRESHOLD:
        return "WARM"
    return "COLD"


def schedule():
    actions = []
    for path in sorted(config.DEVICE.iterdir()):
        if not path.is_file():
            continue

        previous_temp = temperature_store.get(path.name, 700.0)
        last_access = _last_access_timestamp(path)
        temp = calculate_temperature(previous_temp, last_access)
        temperature_store[path.name] = temp

        tier = classify_temperature(temp)
        if tier == "COLD":
            record = cloud_storage.archive_cold_file(path, temp)
            actions.append({"filename": path.name, "tier": tier, "target": "cloud", "temperature": round(temp, 2), "record": record})
        elif tier == "WARM":
            destination = cloud_storage.move_to_edge(path, temp)
            actions.append({"filename": path.name, "tier": tier, "target": "edge", "temperature": round(temp, 2), "record": {"path": str(destination)}})
        else:
            actions.append({"filename": path.name, "tier": tier, "target": "device", "temperature": round(temp, 2)})

    return actions


def snapshot():
    return {
        "device": [path.name for path in config.DEVICE.iterdir() if path.is_file()],
        "edge": [path.name for path in config.EDGE.iterdir() if path.is_file()],
        "cloud": [path.name for path in config.CLOUD.iterdir() if path.is_file() and path.name != "index.json"],
        "compressed": [path.name for path in config.COMPRESSED.iterdir() if path.is_file()],
        "encrypted": [path.name for path in config.ENCRYPTED.iterdir() if path.is_file()],
        "cloud_records": cloud_storage.get_cloud_records(),
        "temperature_store": dict(sorted(temperature_store.items())),
    }
