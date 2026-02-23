import joblib
from datetime import datetime, timedelta

from database import (
    get_logged_hours,
    generate_execution_units,
    get_pending_units,
    update_predicted_completion
)

from milestone_graph import compute_criticality, filter_unlocked_milestones
from execution_phase import compute_execution_phase


MODEL_PATH = "deadline_risk_model.pkl"
BASE_CAPACITY = 6
MIN_CAPACITY = 2
MAX_CAPACITY = 10

model = joblib.load(MODEL_PATH)


def compute_adaptive_capacity():
    return BASE_CAPACITY, False, 0


def generate_operator_briefing(milestones):

    today = datetime.now()
    adaptive_capacity, _, _ = compute_adaptive_capacity()
    phase = compute_execution_phase()

    print("\n===== OPERATOR BRIEFING =====\n")
    print(f"Adaptive Capacity: {adaptive_capacity} hrs")
    print(f"Execution Phase: {phase}\n")

    milestones = filter_unlocked_milestones(milestones)
    criticality_map = compute_criticality()

    plan = []
    hours_left = adaptive_capacity

    for m in milestones:

        logged = get_logged_hours(m["id"])
        remaining = m["total_hours"] - logged

        if remaining <= 0:
            continue

        pending_units = get_pending_units(m["id"])

        if not pending_units:
            generate_execution_units(
                m["id"],
                remaining,
                adaptive_capacity,
                phase
            )
            pending_units = get_pending_units(m["id"])

        required_daily = remaining / 5
        predicted_days = remaining / max(required_daily, 0.01)
        predicted_completion = today + timedelta(days=predicted_days)
        update_predicted_completion(m["id"], predicted_completion.isoformat())

        criticality = criticality_map.get(m["id"], 0)
        priority_score = required_daily * (1 + criticality)

        for unit in pending_units:
            if hours_left <= 0:
                break

            if unit["hours"] <= hours_left:
                plan.append((m["id"], unit["id"], unit["hours"]))
                hours_left -= unit["hours"]

    print("===== TODAY'S EXECUTION PLAN =====\n")

    for milestone_id, unit_id, hours in plan:
        print(f"- Milestone {milestone_id} | Unit {unit_id} → {hours} hrs")

    print("\n===================================\n")

    return plan