from datetime import datetime
from database import get_logged_hours

DAILY_WORK_HOURS = 6


def schedule(milestones):
    today = datetime.now()
    scored = []

    for m in milestones:
        logged = get_logged_hours(m["id"])
        remaining = m["total_hours"] - logged

        if remaining <= 0:
            continue

        deadline = datetime.fromisoformat(m["deadline"])
        days_remaining = (deadline - today).days

        if days_remaining <= 0:
            days_remaining = 1

        required_daily = remaining / days_remaining

        scored.append((required_daily, m, remaining))

    scored.sort(reverse=True, key=lambda x: x[0])

    plan = []
    hours_left = DAILY_WORK_HOURS

    for urgency, m, remaining in scored:
        if hours_left <= 0:
            break

        allocate = min(urgency, remaining, hours_left)
        plan.append((m, round(allocate, 2)))
        hours_left -= allocate

    return plan
