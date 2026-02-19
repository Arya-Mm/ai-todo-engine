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

    # ---------------- ANALYSIS LOOP ----------------

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

        # ---------------- EMBEDDING ----------------
        embedding = compute_execution_embedding(m, adaptive_capacity)

        # ---------------- FEASIBILITY ----------------
        max_possible_output = adaptive_capacity * days_remaining
        infeasible = remaining > max_possible_output

        # ---------------- DEADLINE LOAD ----------------
        if infeasible:
            deadline_load = "🚫 IMPOSSIBLE"
        elif required_daily > adaptive_capacity:
            deadline_load = "⚠ DEADLINE IMPOSSIBLE"
        elif required_daily > adaptive_capacity * 0.7:
            deadline_load = "⚡ HIGH LOAD"
        else:
            deadline_load = "OK"

        # ---------------- ML FORECAST ----------------
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

        # ---------------- OUTPUT ----------------
        print(f"Milestone: {m['title']}")
        print(f"  Remaining Hours: {round(remaining,2)}")
        print(f"  Days Remaining: {days_remaining}")
        print(f"  Required Daily: {round(required_daily,2)} hrs/day")
        print(f"  7-Day Velocity: {round(actual_velocity,2)} hrs/day")
        print(f"  Completion: {round(completion_percent,2)}%")
        print(f"  Deadline Load: {deadline_load}")
        print(f"  Forecast: {forecast} ({confidence}% confidence)\n")

        # ---------------- URGENCY SCORE (fallback ranking only) ----------------
        urgency_score = required_daily

        if velocity_active:
            velocity_gap = required_daily - actual_velocity
            urgency_score += velocity_gap * VELOCITY_CORRECTION_FACTOR

        if slippage_flag:
            urgency_score *= 0.8

        if infeasible:
            urgency_score = required_daily * 1.2  # force priority

        scored.append((urgency_score, m["id"]))

        context_data[m["id"]] = {
            "remaining": remaining,
            "days_remaining": days_remaining,
            "required_daily": required_daily,
            "actual_velocity": actual_velocity,
            "forecast": forecast,
            "embedding": embedding
        }

    # ---------------- SORT BY URGENCY ----------------

    scored.sort(reverse=True, key=lambda x: x[0])

    plan = []
    hours_left = adaptive_capacity

    print("===== TODAY'S EXECUTION PLAN =====\n")

    for _, milestone_id in scored:

        if hours_left <= 0:
            break

        ctx = context_data[milestone_id]

        embedding_state = ctx["embedding"]

        # ---------------- RL DECISION ----------------
        rl_allocation = choose_allocation(embedding_state, adaptive_capacity)

        if rl_allocation is None:
            # fallback deterministic
            allocate = min(ctx["required_daily"], ctx["remaining"], hours_left)
        else:
            allocate = min(rl_allocation, ctx["remaining"], hours_left)

        plan.append((milestone_id, round(allocate, 2)))
        hours_left -= allocate

    # ---------------- OUTPUT + LOGGING ----------------

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
