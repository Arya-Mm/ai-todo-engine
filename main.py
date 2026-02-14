from database import (
    init_db,
    add_goal,
    add_milestone,
    get_goals,
    get_milestones,
    log_work
)
from scheduler import generate_operator_briefing


def safe_float(prompt):
    while True:
        value = input(prompt).strip()
        try:
            return float(value)
        except ValueError:
            print("Invalid number. Try again.")


def safe_int(prompt):
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print("Invalid integer. Try again.")


def menu():
    print("\n1. Add Goal")
    print("2. Add Milestone to Goal")
    print("3. Generate Operator Briefing")
    print("4. Log Work")
    print("5. Exit")


if __name__ == "__main__":
    init_db()

    while True:
        menu()
        choice = input("Select option: ").strip()

        # -------- ADD GOAL --------
        if choice == "1":
            title = input("Goal Title: ").strip()
            if not title:
                print("Title cannot be empty.")
                continue

            deadline_days = safe_float("Deadline in days: ")
            if deadline_days <= 0:
                print("Deadline must be positive.")
                continue

            add_goal(title, deadline_days)
            print("Goal added.")

        # -------- ADD MILESTONE --------
        elif choice == "2":
            goals = get_goals()

            if not goals:
                print("No goals found. Add a goal first.")
                continue

            print("\nAvailable Goals:")
            for g in goals:
                print(f"{g['id']} → {g['title']}")

            goal_id = safe_int("Goal ID: ")

            if goal_id not in [g["id"] for g in goals]:
                print("Invalid Goal ID.")
                continue

            title = input("Milestone Title: ").strip()
            if not title:
                print("Milestone title cannot be empty.")
                continue

            hours = safe_float("Total hours required: ")
            if hours <= 0:
                print("Hours must be positive.")
                continue

            add_milestone(goal_id, title, hours)
            print("Milestone added.")

        # -------- OPERATOR BRIEFING --------
        elif choice == "3":
            milestones = get_milestones()

            if not milestones:
                print("No milestones found.")
                continue

            generate_operator_briefing(milestones)

        # -------- LOG WORK --------
        elif choice == "4":
            milestones = get_milestones()

            if not milestones:
                print("No milestones found.")
                continue

            print("\nAvailable Milestones:")
            for m in milestones:
                print(f"{m['id']} → {m['title']}")

            milestone_id = safe_int("Milestone ID: ")

            if milestone_id not in [m["id"] for m in milestones]:
                print("Invalid Milestone ID.")
                continue

            hours = safe_float("Hours worked: ")
            if hours <= 0:
                print("Hours must be positive.")
                continue

            log_work(milestone_id, hours)
            print("Work logged.")

        # -------- EXIT --------
        elif choice == "5":
            print("Exiting.")
            break

        else:
            print("Invalid option. Choose 1-5.")
