def compute_reward(
    prev_required_daily,
    new_required_daily,
    performance_ratio,
    prev_forecast,
    new_forecast,
    completed
):
    reward = 0

    # ---- Risk Delta ----
    risk_delta = prev_required_daily - new_required_daily
    reward += risk_delta * 2

    # ---- Performance ----
    if performance_ratio >= 1:
        reward += 2
    elif performance_ratio >= 0.8:
        reward += 1
    elif performance_ratio < 0.6:
        reward -= 2

    # ---- Forecast Movement ----
    forecast_map = {
        "SAFE": 0,
        "⚠ AT RISK": 1,
        "🚨 WILL MISS DEADLINE": 2,
        "🚫 MATHEMATICALLY INFEASIBLE": 2
    }

    if prev_forecast in forecast_map and new_forecast in forecast_map:
        delta = forecast_map[prev_forecast] - forecast_map[new_forecast]
        reward += delta * 3

    # ---- Completion ----
    if completed:
        reward += 10

    return round(reward, 3)
