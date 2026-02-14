from datetime import datetime
from database import get_logged_hours

DAILY_WORK_HOURS = 6


def generate_operator_briefing(milestones):
    today = datetime.now()
    scored = []

    print("\n===== OPERATOR BRIEFING =====\n")

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
        completion_percent = (logged / m["total_hours"]) * 100

        # Risk level
        if required_daily > DAILY_WORK_HOURS:
            risk = "⚠ HIGH RISK"
        elif required_daily > DAILY_WORK_HOURS * 0.7:
            risk = "⚡ MEDIUM RISK"
        else:
            risk = "✅ STABLE"

        print(f"Milestone: {m['title']}")
        print(f"  Remaining Hours: {round(remaining,2)}")
        print(f"  Days Remaining: {days_remaining}")
        print(f"  Required Daily: {round(required_daily,2)} hrs/day")
        print(f"  Completion: {round(completion_percent,2)}%")
        print(f"  Status: {risk}")
        print("")

        scored.append((required_daily, m, remaining))

    # Sort by urgency
    scored.sort(reverse=True, key=lambda x: x[0])

    # Build today's plan
    plan = []
    hours_left = DAILY_WORK_HOURS

    for urgency, m, remaining in scored:
        if hours_left <= 0:
            break

        allocate = min(urgency, remaining, hours_left)
        plan.append((m, round(allocate, 2)))
        hours_left -= allocate

    print("===== TODAY'S EXECUTION PLAN =====\n")
    for m, hours in plan:
        print(f"- {m['title']} → {hours} hrs (ID: {m['id']})")

    print("\n===================================\n")

    return plan
