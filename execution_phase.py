from database import get_recent_performance

SLIPPAGE_THRESHOLD = 0.7
SURGE_THRESHOLD = 1.1
COLLAPSE_STREAK_LIMIT = 3


def compute_execution_phase():
    """
    Classifies current behavioral phase:
    STABLE / SURGE / COLLAPSE
    """

    performances = get_recent_performance(7)

    if not performances:
        return "STABLE"

    streak_under = 0
    streak_over = 0

    for ratio in performances:
        if ratio is None:
            continue

        if ratio < SLIPPAGE_THRESHOLD:
            streak_under += 1
            streak_over = 0
        elif ratio > SURGE_THRESHOLD:
            streak_over += 1
            streak_under = 0
        else:
            streak_under = 0
            streak_over = 0

    # ---- Collapse ----
    if streak_under >= COLLAPSE_STREAK_LIMIT:
        return "COLLAPSE"

    # ---- Surge ----
    if streak_over >= 2:
        return "SURGE"

    return "STABLE"
