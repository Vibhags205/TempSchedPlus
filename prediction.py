from __future__ import annotations

from statistics import mean


def _predict_from_temperature_series(temperatures):
    if not temperatures:
        return 500.0

    values = [float(value) for value in temperatures]
    current_mean = mean(values)
    hot_ratio = sum(1 for value in values if value >= 600) / len(values)
    cold_ratio = sum(1 for value in values if value < 400) / len(values)
    trend = 0.0
    if len(values) >= 2:
        trend = (values[-1] - values[0]) * 0.25

    predicted = current_mean + (hot_ratio * 120.0) - (cold_ratio * 80.0) + trend
    return max(300.0, min(800.0, predicted))


def _predict_from_file_info(file_info):
    last_access = float(file_info.get("last_access", 0.0))
    last_modified = float(file_info.get("last_modified", last_access))
    size = float(file_info.get("size", 0.0))

    age_seconds = max(last_modified - last_access, 0.0)
    age_score = min(age_seconds / 86400.0, 30.0)
    size_score = min(size / 1024.0 / 1024.0, 500.0)

    # Lower scores mean hotter data; higher scores mean colder data.
    predicted = 780.0 - (age_score * 12.0) - (size_score * 2.0)
    return max(300.0, min(800.0, predicted))


def predict(temperatures=None):
    """Predict the next temperature using the real temperature series.

    If a list or mapping of temperatures is provided, the prediction is derived
    from those values. Otherwise a stable default forecast is returned.
    """
    if temperatures is None:
        return 500.0

    if isinstance(temperatures, dict):
        if {"last_access", "last_modified", "size"}.issubset(temperatures.keys()):
            return round(_predict_from_file_info(temperatures), 2)
        temperatures = temperatures.values()

    return round(_predict_from_temperature_series(list(temperatures)), 2)
