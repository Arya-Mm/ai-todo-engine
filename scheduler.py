import joblib
import numpy as np
from datetime import datetime

from database import (
    get_logged_hours,
    get_recent_velocity,
    get_log_count,
    get_recent_daily_output,
    get_recent_performance,
    log_plan
)

from reinforcement_allocator import choose_allocation
from state_embedding import compute_execution_embedding


# ==============================
# CONFIG
# ==============================

MODEL_PATH = "deadline_risk_model.pkl"

BASE_CAPACITY = 6
MIN_CAPACITY = 2
MAX_CAPACITY = 10

VELOCITY_CORRECTION_FACTOR = 0.5
VELOCITY_MIN_LOGS = 3

SLIPPAGE_THRESHOLD = 0.7
SLIPPAGE_STREAK_LIMIT = 3

model = joblib.load(MODEL_PATH)


# ==============================
# SLIPPAGE DETECTION
# ==============================

def detect_slippage_streak():
    performances = get_recent_performance(7)

    streak = 0
    for ratio in performances:
        if ratio is not None and ratio < SLIPPAGE_THRESHOLD:
            streak += 1
        else:
            break

    return streak >= SLIPPAGE_STREAK_LIMIT, streak


# ==============================
# ADAPTIVE CAPACITY
# ==============================

def compute_adaptive_capacity():
    recent_7 = get_recent_daily_output(7)
    recent_3 = get_recent_daily_output(3)

    baseline = max(recent_7, recent_3)
    capacity = BASE_CAPACITY if baseline == 0 else baseline

    slippage_flag, streak = detect_slippage_streak()

    if slippage_flag:
        capacity *= 0.8

    capacity = max(MIN_CAPACITY, capacity)
    capacity = min(MAX_CAPACITY, capacity)

    return round(capacity, 2), slippage_flag, streak


# ==============================
# OPERATOR BRIEFING
# ==============================

def generate_operator_briefing(milestones):

    today = datetime.now()
    scored = []
    context_data = {}

    adaptive_capacity, slippage_flag, streak = compute_adaptive_capacity()

    print("\n===== OPERATOR BRIEFING =====\n")
    print(f"Adaptive Daily Capacity: {adaptive_capacity} hrs")

    if slippage_flag:
        print(f"⚠ SLIPPAGE DETECTED: {streak}-day underperformance streak\n")
    else:
        print("")

    # -------------------------
    # ANALYSIS LOOP
    # -------------------------

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

        # -------------------------
        # FEASIBILITY CHECK
        # -------------------------

        max_possible_output = adaptive_capacity * days_remaining
        infeasible = remaining > max_possible_output

        # -------------------------
        # DEADLINE LOAD
        # -------------------------

        if infeasible:
            deadline_load = "🚫 IMPOSSIBLE"
        elif required_daily > adaptive_capacity:
            deadline_load = "⚠ DEADLINE IMPOSSIBLE"
        elif required_daily > adaptive_capacity * 0.7:
            deadline_load = "⚡ HIGH LOAD"
        else:
            deadline_load = "OK"

        # -------------------------
        # ML FORECAST
        # -------------------------

        if infeasible:
            forecast = "🚫 MATHEMATICALLY INFEASIBLE"
            confidence = 100.0

        elif velocity_active:

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
            probabilities = model.predict_proba(feature_vector)[0]

            label_map = {
                0: "SAFE",
                1: "⚠ AT RISK",
                2: "🚨 WILL MISS DEADLINE"
            }

            forecast = label_map[prediction]
            confidence = round(max(probabilities) * 100, 2)

        else:
            forecast = "INSUFFICIENT DATA"
            confidence = 0.0

        # -------------------------
        # EXECUTION STATE EMBEDDING
        # -------------------------

        embedding = compute_execution_embedding(
            remaining,
            days_remaining,
            required_daily,
            actual_velocity,
            adaptive_capacity,
            slippage_flag
        )

        # -------------------------
        # OUTPUT
        # -------------------------

        print(f"Milestone: {m['title']}")
        print(f"  Remaining Hours: {round(remaining,2)}")
        print(f"  Days Remaining: {days_remaining}")
        print(f"  Required Daily: {round(required_daily,2)} hrs/day")
        print(f"  7-Day Velocity: {round(actual_velocity,2)} hrs/day")
        print(f"  Completion: {round(completion_percent,2)}%")
        print(f"  Deadline Load: {deadline_load}")
        print(f"  Forecast: {forecast} ({confidence}% confidence)")

        if infeasible:
            extra_hours = round(remaining - max_possible_output, 2)
            required_capacity = round(remaining / days_remaining, 2)
            extra_days = round((remaining / adaptive_capacity) - days_remaining, 2)

            print("  ⚠ ENFORCEMENT REQUIRED")
            print(f"  Extra Hours Beyond Capacity: {extra_hours}")
            print(f"  Required Daily Capacity: {required_capacity} hrs/day")
            print(f"  Deadline Extension Needed: {extra_days} days")

        print("")

        # -------------------------
        # URGENCY SCORE
        # -------------------------

        if velocity_active:
            velocity_gap = required_daily - actual_velocity
            adjusted_required = required_daily + (
                velocity_gap * VELOCITY_CORRECTION_FACTOR
            )
        else:
            adjusted_required = required_daily

        if slippage_flag:
            adjusted_required *= 0.7

        if infeasible:
            adjusted_required = required_daily

        scored.append((adjusted_required, m["id"], remaining, embedding))

        context_data[m["id"]] = {
            "remaining": remaining,
            "days_remaining": days_remaining,
            "required_daily": required_daily,
            "actual_velocity": actual_velocity,
            "forecast": forecast
        }

    # -------------------------
    # SORT BY URGENCY
    # -------------------------

    scored.sort(reverse=True, key=lambda x: x[0])

    plan = []
    hours_left = adaptive_capacity

    print("===== TODAY'S EXECUTION PLAN =====\n")

    for urgency, milestone_id, remaining, embedding in scored:

        if hours_left <= 0:
            break

        # RL Allocation Decision
        rl_alloc = choose_allocation(embedding, adaptive_capacity)

        if rl_alloc is not None:
            allocate = min(rl_alloc, remaining, hours_left)
        else:
            allocate = min(urgency, remaining, hours_left)

        plan.append((milestone_id, round(allocate, 2)))
        hours_left -= allocate

    # -------------------------
    # OUTPUT + LOGGING
    # -------------------------

    for milestone_id, hours in plan:

        print(f"- ID {milestone_id} → {hours} hrs")

        ctx = context_data[milestone_id]

        log_plan(
            milestone_id=milestone_id,
            remaining=ctx["remaining"],
            days_remaining=ctx["days_remaining"],
            required_daily=ctx["required_daily"],
            actual_velocity=ctx["actual_velocity"],
            allocated=hours,
            forecast=ctx["forecast"]
        )

    print("\n===================================\n")

    return plan
