from database import init_db
from scheduler import schedule_tasks

def get_sample_tasks():
    return [
        {"title": "DSA Practice", "est_duration": 2, "deadline_hours": 24, "value_score": 8, "difficulty": 6, "energy_required": 7},
        {"title": "Gym", "est_duration": 1.5, "deadline_hours": 48, "value_score": 7, "difficulty": 5, "energy_required": 6},
        {"title": "AI Project", "est_duration": 3, "deadline_hours": 12, "value_score": 10, "difficulty": 8, "energy_required": 8},
        {"title": "Internship Application", "est_duration": 1, "deadline_hours": 6, "value_score": 9, "difficulty": 4, "energy_required": 5}
    ]

if __name__ == "__main__":
    init_db()

    tasks = get_sample_tasks()

    schedule = schedule_tasks(tasks, available_time=4, user_energy=7)

    print("\nToday's Optimal Schedule:\n")
    for t in schedule:
        print("-", t["title"])
