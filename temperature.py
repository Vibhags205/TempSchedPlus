import math
import time

def calculate_temperature(old_temp, last_access):

    k = 0.01
    gamma = 500

    time_gap = time.time() - last_access

    new_temp = old_temp * math.exp(-k * time_gap)

    return new_temp + gamma
