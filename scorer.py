def calculate_priority(task, user_energy=5):
    urgency = 1 / (task["deadline_hours"] + 1)

    energy_match = 1 - abs(user_energy - task["energy_required"]) / 10

    score = (
        urgency * 0.4 +
        task["value_score"] * 0.3 -
        task["difficulty"] * 0.1 +
        energy_match * 0.2
    )

    return score
