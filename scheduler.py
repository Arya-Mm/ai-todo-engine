from datetime import datetime
from database import get_logged_hours


DAILY_WORK_HOURS = 6  # system-controlled


def schedule(tasks):
    today = datetime.now()
    scored = []

    for task in tasks:
        logged = get_logged_hours(task["id"])
        remaining_hours = task["total_hours"] - logged

        if remaining_hours <= 0:
            continue

        deadline = datetime.fromisoformat(task["deadline"])
        days_remaining = (deadline - today).days

        if days_remaining <= 0:
            days_remaining = 1

        required_daily = remaining_hours / days_remaining

        scored.append((required_daily, task, remaining_hours))

    scored.sort(reverse=True, key=lambda x: x[0])

    plan = []
    hours_left_today = DAILY_WORK_HOURS

    for urgency, task, remaining in scored:
        if hours_left_today <= 0:
            break

        allocate = min(urgency, hours_left_today, remaining)
        plan.append((task, round(allocate, 2)))
        hours_left_today -= allocate

    return plan
