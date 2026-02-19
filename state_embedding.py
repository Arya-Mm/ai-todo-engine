import numpy as np

def compute_execution_embedding(
    remaining,
    days_remaining,
    required_daily,
    actual_velocity,
    adaptive_capacity,
    phase
):
    remaining_ratio = remaining / (remaining + 1)
    pressure = required_daily / adaptive_capacity
    velocity_gap = required_daily - actual_velocity

    phase_map = {
        "STABLE": [1, 0, 0],
        "SURGE": [0, 1, 0],
        "COLLAPSE": [0, 0, 1]
    }

    phase_vec = phase_map.get(phase, [1, 0, 0])

    embedding = np.array([
        remaining,
        days_remaining,
        required_daily,
        actual_velocity,
        remaining_ratio,
        pressure,
        velocity_gap,
        adaptive_capacity,
        *phase_vec
    ])

    # Pad to 14 features
    while len(embedding) < 14:
        embedding = np.append(embedding, 0)

    return embedding
