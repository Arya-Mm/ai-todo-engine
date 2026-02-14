from datetime import datetime
from database import get_logged_hours, get_recent_velocity
import sqlite3

DAILY_WORK_HOURS = 6
VELOCITY_CORRECTION_FACTOR = 0.5
VELOCITY_MIN_LOGS = 3


def get_log_count(milestone_id):
    conn = sqlite3.connect("tasks.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM logs WHERE milestone_id = ?", (milestone_id,))
    count = c.fetchone()[0]
    conn.close()
    return count


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
        log_count = get_log_count(m["id"])
        completion_percent = (logged / m["total_hours"]) * 100

        velocity_active = log_count >= VELOCITY_MIN_LOGS and actual_velocity > 0

        # ----- Deadline Load -----
        if required_daily > DAILY_WORK_HOURS:
            deadline_load = "⚠ DEADLINE IMPOSSIBLE"
        elif required_daily > DAILY_WORK_HOURS * 0.7:
            deadline_load = "⚡ HIGH LOAD"
        else:
            deadline_load = "OK"

        # ----- Forecast -----
        if velocity_active:
            projected_days_needed = remaining / actual_velocity

            if projected_days_needed > days_remaining:
                forecast = "🚨 WILL MISS DEADLINE"
            elif projected_days_needed > days_remaining * 0.8:
                forecast = "⚠ AT RISK"
            else:
                forecast = "SAFE"
        else:
            forecast = "INSUFFICIENT DATA"

        print(f"Milestone: {m['title']}")
        print(f"  Remaining Hours: {round(remaining,2)}")
        print(f"  Days Remaining: {days_remaining}")
        print(f"  Required Daily: {round(required_daily,2)} hrs/day")
        print(f"  7-Day Velocity: {round(actual_velocity,2)} hrs/day")
        print(f"  Completion: {round(completion_percent,2)}%")
        print(f"  Deadline Load: {deadline_load}")
        print(f"  Deadline Forecast: {forecast}")

        # ----- Recovery Planner -----
        if velocity_active and forecast == "🚨 WILL MISS DEADLINE":
            required_velocity_to_recover = required_daily
            days_needed = remaining / actual_velocity
            extra_days_required = round(days_needed - days_remaining, 2)

            max_possible = actual_velocity * days_remaining
            scope_cut = round(remaining - max_possible, 2)

            print("  --- RECOVERY OPTIONS ---")
            print(f"  1) Increase daily output to: {round(required_velocity_to_recover,2)} hrs/day")
            print(f"  2) Extend deadline by: {extra_days_required} days")
            print(f"  3) Reduce scope by: {scope_cut} hours")
        print("")

        # ----- Adaptive Allocation -----
        if velocity_active:
            velocity_gap = required_daily - actual_velocity
            adjusted_required = required_daily + (velocity_gap * VELOCITY_CORRECTION_FACTOR)
        else:
            adjusted_required = required_daily

        scored.append((adjusted_required, m, remaining))

    scored.sort(reverse=True, key=lambda x: x[0])

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
