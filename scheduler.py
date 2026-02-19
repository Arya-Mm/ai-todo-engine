import joblib
import numpy as np
from datetime import datetime

from database import (
    get_logged_hours,
    get_recent_velocity,
    get_log_count,
    get_recent_daily_output,
    get_recent_performance,
    get_last_plan_state,
    update_plan_reward,
    log_plan,
    log_transition,
    compute_reward
)

from reinforcement_allocator import (
    choose_allocation,
    td_update
)

from state_embedding import compute_execution_embedding


# ==================================================
# CONFIG
# ==================================================

MODEL_PATH = "deadline_risk_model.pkl"

BASE_CAPACITY = 6
MIN_CAPACITY = 2
MAX_CAPACITY = 10

VELOCITY_CORRECTION_FACTOR = 0.5
VELOCITY_MIN_LOGS = 3

SLIPPAGE_THRESHOLD = 0.7
SLIPPAGE_STREAK_LIMIT = 3

model = joblib.load(MODEL_PATH)


# ==================================================
# EXECUTION PHASE CLASSIFIER
# ==================================================

def compute_execution_phase():
    performances = get_recent_performance(7)

    if not performances:
        return "STABLE"

    under_streak = 0
    over_streak = 0

    for ratio in performances:
        if ratio is None:
            continue

        if ratio < SLIPPAGE_THRESHOLD:
            under_streak += 1
            over_streak = 0
        elif ratio > 1.1:
            over_streak += 1
            under_streak = 0
        else:
            under_streak = 0
            over_streak = 0

    if under_streak >= SLIPPAGE_STREAK_LIMIT:
        return "COLLAPSE"

    if over_streak >= 2:
        return "SURGE"

    return "STABLE"


# ==================================================
# ADAPTIVE CAPACITY
# ==================================================

def compute_adaptive_capacity():
    recent_7 = get_recent_daily_output(7)
    recent_3 = get_recent_daily_output(3)

    baseline = max(recent_7, recent_3)
    capacity = BASE_CAPACITY if baseline == 0 else baseline

    phase = compute_execution_phase()

    if phase == "COLLAPSE":
        capacity *= 0.7
    elif phase == "SURGE":
        capacity *= 1.1

    capacity = max(MIN_CAPACITY, capacity)
    capacity = min(MAX_CAPACITY, capacity)

    return round(capacity, 2), phase


# ==================================================
# MAIN EXECUTION LOOP
# ==================================================

def generate_operator_briefing(milestones):

    today = datetime.now()
    scored = []
    context_data = {}

    adaptive_capacity, phase = compute_adaptive_capacity()

    print("\n===== OPERATOR BRIEFING =====\n")
    print(f"Execution Phase: {phase}")
    print(f"Adaptive Daily Capacity: {adaptive_capacity} hrs\n")

    # ------------------------------------------
    # ANALYSIS
    # ------------------------------------------

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

        velocity_active = log_count >= VELOCITY_MIN_LOGS and actual_velocity > 0

        # ------------------------------------------
        # FORECAST
        # ------------------------------------------

        if velocity_active:

            velocity_gap = required_daily - actual_velocity
            remaining_ratio = remaining / (remaining + 1)
            workload_pressure = required_daily / adaptive_capacity
            allocation_ratio = required_daily / adaptive_capacity

            feature_vector = np.array([[
                remaining,
                days_remaining,
                required_daily,
                actual_velocity,
                velocity_gap,
                remaining_ratio,
                workload_pressure,
                allocation_ratio
            ]])

            prediction = model.predict(feature_vector)[0]

            label_map = {
                0: "SAFE",
                1: "⚠ AT RISK",
                2: "🚨 WILL MISS DEADLINE"
            }

            forecast = label_map[prediction]

        else:
            forecast = "INSUFFICIENT DATA"

        # ------------------------------------------
        # EMBEDDING
        # ------------------------------------------

        embedding = compute_execution_embedding(
            remaining,
            days_remaining,
            required_daily,
            actual_velocity,
            adaptive_capacity,
            phase
        )

        # ------------------------------------------
        # URGENCY
        # ------------------------------------------

        if velocity_active:
            velocity_gap = required_daily - actual_velocity
            urgency = required_daily + (
                velocity_gap * VELOCITY_CORRECTION_FACTOR
            )
        else:
            urgency = required_daily

        scored.append((urgency, m["id"], remaining, embedding))

        context_data[m["id"]] = {
            "remaining": remaining,
            "days_remaining": days_remaining,
            "required_daily": required_daily,
            "actual_velocity": actual_velocity,
            "forecast": forecast,
            "embedding": embedding
        }

    # ------------------------------------------
    # SORT BY URGENCY
    # ------------------------------------------

    scored.sort(reverse=True, key=lambda x: x[0])

    plan = []
    hours_left = adaptive_capacity

    print("===== TODAY'S EXECUTION PLAN =====\n")

    for urgency, milestone_id, remaining, embedding in scored:

        if hours_left <= 0:
            break

        action = choose_allocation(embedding, adaptive_capacity)

        if action is not None:
            allocate = min(action, remaining, hours_left)
        else:
            allocate = min(urgency, remaining, hours_left)

        plan.append((milestone_id, round(allocate, 2)))
        hours_left -= allocate

    # ------------------------------------------
    # EXECUTION + TD UPDATE
    # ------------------------------------------

    for milestone_id, hours in plan:

        ctx = context_data[milestone_id]

        print(f"- ID {milestone_id} → {hours} hrs")

        # 1️⃣ Log plan
        log_plan(
            milestone_id=milestone_id,
            remaining=ctx["remaining"],
            days_remaining=ctx["days_remaining"],
            required_daily=ctx["required_daily"],
            actual_velocity=ctx["actual_velocity"],
            allocated=hours,
            forecast=ctx["forecast"]
        )

        # 2️⃣ Get previous state
        prev_state_data = get_last_plan_state(milestone_id)

        if prev_state_data:

            prev_embedding = ctx["embedding"]
            prev_required_daily = prev_state_data["required_daily"]
            prev_forecast = prev_state_data["forecast"]

            # simulate next state after allocation
            new_remaining = ctx["remaining"] - hours
            new_required_daily = new_remaining / ctx["days_remaining"]

            next_embedding = compute_execution_embedding(
                new_remaining,
                ctx["days_remaining"],
                new_required_daily,
                ctx["actual_velocity"],
                adaptive_capacity,
                phase
            )

            # 3️⃣ Compute reward
            reward = compute_reward(
                prev_required_daily,
                new_required_daily,
                performance_ratio=1,  # simplified for now
                prev_forecast=prev_forecast,
                new_forecast=ctx["forecast"],
                completed=new_remaining <= 0
            )

            # 4️⃣ Update plan reward
            update_plan_reward(prev_state_data["plan_id"], reward)

            # 5️⃣ Log transition
            log_transition(
                milestone_id,
                prev_embedding,
                hours,
                reward,
                next_embedding
            )

            # 6️⃣ TD update
            td_update(
                prev_embedding,
                hours,
                reward,
                next_embedding
            )

    print("\n===================================\n")

    return plan
