from __future__ import annotations

from statistics import mean


def _current_from_temperature_series(temperatures):
    if not temperatures:
        return 500.0

    values = [float(value) for value in temperatures]
    if len(values) == 1:
        return max(300.0, min(800.0, values[0]))

    # Emphasize recent values to represent the current state.
    recent_values = values[-5:]
    recent_mean = mean(recent_values)
    latest = values[-1]
    current = (recent_mean * 0.4) + (latest * 0.6)
    return max(300.0, min(800.0, current))


def _estimate_from_file_info(file_info):
    last_access = float(file_info.get("last_access", 0.0))
    last_modified = float(file_info.get("last_modified", last_access))
    size = float(file_info.get("size", 0.0))

    age_seconds = max(last_modified - last_access, 0.0)
    age_score = min(age_seconds / 86400.0, 30.0)
    size_score = min(size / 1024.0 / 1024.0, 500.0)

    # Lower scores mean hotter data; higher scores mean colder data.
    estimated = 780.0 - (age_score * 12.0) - (size_score * 2.0)
    return max(300.0, min(800.0, estimated))


def current_temperature(temperatures=None):
    """Estimate current temperature from observed temperature values or file features."""
    if temperatures is None:
        return 500.0

    if isinstance(temperatures, dict):
        if {"last_access", "last_modified", "size"}.issubset(temperatures.keys()):
            return round(_estimate_from_file_info(temperatures), 2)
        temperatures = temperatures.values()

    return round(_current_from_temperature_series(list(temperatures)), 2)


def predict(temperatures=None):
    """Backward-compatible alias for current temperature estimation."""
    return current_temperature(temperatures)
