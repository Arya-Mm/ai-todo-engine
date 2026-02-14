from scorer import calculate_priority


def schedule_tasks(tasks, available_time):
    scored = []

    for t in tasks:
        score = calculate_priority(t)
        scored.append((score, t))

    scored.sort(reverse=True, key=lambda x: x[0])

    scheduled = []
    time_used = 0

    for score, task in scored:
        if time_used + task["est_duration"] <= available_time:
            scheduled.append(task)
            time_used += task["est_duration"]

    return scheduled
