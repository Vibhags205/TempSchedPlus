import math
import time

import config

def calculate_temperature(old_temp, last_access):
    # Newton-style cooling: relax current hotness toward ambient over time.
    decay_rate = float(config.TEMP_DECAY_RATE_PER_HOUR)
    ambient = float(config.TEMP_AMBIENT)

    time_gap_seconds = max(time.time() - float(last_access), 0.0)
    time_gap_hours = time_gap_seconds / 3600.0

    return ambient + (float(old_temp) - ambient) * math.exp(-decay_rate * time_gap_hours)
