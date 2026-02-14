from datetime import datetime


def calculate_priority(task):
    deadline = datetime.fromisoformat(task["deadline"])
    hours_remaining = (deadline - datetime.now()).total_seconds() / 3600

    # Prevent negative explosion if overdue
    if hours_remaining < 0:
        hours_remaining = 0

    urgency = 1 / (hours_remaining + 1)

    score = (
        urgency * 0.5 +
        task["value_score"] * 0.3 -
        task["difficulty"] * 0.2
    )

    return score
