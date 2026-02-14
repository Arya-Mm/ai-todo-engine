from database import init_db, add_task, get_pending_tasks
from scheduler import schedule_tasks

def menu():
    print("\n1. Add Task")
    print("2. Generate Schedule")
    print("3. Exit")
    print("4. Mark Task Complete")


if __name__ == "__main__":
    init_db()

    while True:
        menu()
        choice = input("Select option: ")

        if choice == "1":
            title = input("Title: ")
            est = float(input("Estimated duration (hours): "))
            deadline = float(input("Deadline in hours: "))
            value = float(input("Value score (1-10): "))
            difficulty = float(input("Difficulty (1-10): "))
            energy = float(input("Energy required (1-10): "))

            add_task(title, est, deadline, value, difficulty, energy)
            print("Task added.")

        elif choice == "2":
            available = float(input("Available time (hours): "))
            user_energy = float(input("Your current energy (1-10): "))

            tasks = get_pending_tasks()
            schedule = schedule_tasks(tasks, available, user_energy)

            print("\nOptimal Schedule:")
            for t in schedule:
                print(f"- {t['title']} (ID: {t['id']})")

        elif choice == "3":
            break
        elif choice == "4":
            task_id = int(input("Task ID to mark complete: "))
            actual = float(input("Actual duration (hours): "))
            from database import complete_task
            complete_task(task_id, actual)
            print("Task logged and marked complete.")
            break

