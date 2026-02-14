from datetime import datetime
from database import get_logged_hours, get_recent_velocity

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
        actual_velocity = get_recent_velocity(m["id"], days=7)

        velocity_gap = required_daily - actual_velocity
        completion_percent = (logged / m["total_hours"]) * 100

        # Risk logic
        if velocity_gap > required_daily * 0.5:
            risk = "⚠ HIGH RISK (Behind)"
        elif velocity_gap > 0:
            risk = "⚡ MEDIUM RISK"
        else:
            risk = "✅ ON TRACK"

        print(f"Milestone: {m['title']}")
        print(f"  Remaining Hours: {round(remaining,2)}")
        print(f"  Days Remaining: {days_remaining}")
        print(f"  Required Daily: {round(required_daily,2)} hrs/day")
        print(f"  7-Day Velocity: {round(actual_velocity,2)} hrs/day")
        print(f"  Completion: {round(completion_percent,2)}%")
        print(f"  Status: {risk}")
        print("")

        # Adaptive allocation logic
        adjusted_required = required_daily + max(velocity_gap, 0)
        scored.append((adjusted_required, m, remaining))

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
