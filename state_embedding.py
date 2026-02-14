from database import (
    get_recent_velocity,
    get_recent_daily_output,
    get_recent_performance,
    get_logged_hours
)
from datetime import datetime
import numpy as np


# --------------------------------------------------
# EXECUTION STATE EMBEDDING
# --------------------------------------------------

def compute_execution_embedding(milestone, adaptive_capacity):
    """
    Returns normalized execution state vector.
    """

    total_hours = milestone["total_hours"]
    deadline = datetime.fromisoformat(milestone["deadline"])

    logged = get_logged_hours(milestone["id"])
    remaining = total_hours - logged

    days_remaining = (deadline - datetime.now()).days
    if days_remaining <= 0:
        days_remaining = 1

    required_daily = remaining / days_remaining
    actual_velocity = get_recent_velocity(milestone["id"], 7)

    # ---------------- NORMALIZED FEATURES ----------------

    # 1. Remaining Ratio (0–1)
    remaining_ratio = remaining / (total_hours + 1)

    # 2. Deadline Pressure
    deadline_pressure = min(1, required_daily / adaptive_capacity)

    # 3. Velocity Ratio
    velocity_ratio = 0
    if required_daily > 0:
        velocity_ratio = min(1, actual_velocity / required_daily)

    # 4. Slippage Intensity
    performances = get_recent_performance(7)
    if performances:
        slippage_intensity = sum(1 for p in performances if p < 0.7) / len(performances)
    else:
        slippage_intensity = 0

    # 5. Overload Intensity
    recent_output = get_recent_daily_output(7)
    overload_intensity = min(1, recent_output / adaptive_capacity)

    # 6. Performance Trend (momentum)
    if len(performances) >= 2:
        performance_trend = performances[0] - performances[-1]
    else:
        performance_trend = 0

    # 7. Goal Concurrency (proxy via capacity usage)
    goal_concurrency = min(1, required_daily / adaptive_capacity)

    embedding = np.array([
        remaining_ratio,
        deadline_pressure,
        velocity_ratio,
        slippage_intensity,
        overload_intensity,
        performance_trend,
        goal_concurrency
    ])

    return embedding
