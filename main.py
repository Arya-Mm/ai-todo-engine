from database import (
    init_db,
    add_goal,
    add_milestone,
    get_goals,
    get_milestones,
    log_work
)
from scheduler import schedule


def menu():
    print("\n1. Add Goal")
    print("2. Add Milestone to Goal")
    print("3. Generate Today's Plan")
    print("4. Log Work")
    print("5. Exit")


if __name__ == "__main__":
    init_db()

    while True:
        menu()
        choice = input("Select option: ")

        if choice == "1":
            title = input("Goal Title: ")
            deadline_days = float(input("Deadline in days: "))
            add_goal(title, deadline_days)
            print("Goal added.")

        elif choice == "2":
            goals = get_goals()
            for g in goals:
                print(f"{g['id']} → {g['title']}")

            goal_id = int(input("Goal ID: "))
            title = input("Milestone Title: ")
            hours = float(input("Total hours required: "))

            add_milestone(goal_id, title, hours)
            print("Milestone added.")

        elif choice == "3":
            milestones = get_milestones()
            plan = schedule(milestones)

            print("\nToday's Execution Plan:")
            for m, hours in plan:
                print(f"- {m['title']} → {hours} hrs (ID: {m['id']})")

        elif choice == "4":
            milestone_id = int(input("Milestone ID: "))
            hours = float(input("Hours worked: "))
            log_work(milestone_id, hours)
            print("Work logged.")

        elif choice == "5":
            break
