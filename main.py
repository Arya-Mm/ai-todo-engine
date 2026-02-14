from database import init_db, add_task, get_pending_tasks, complete_task
from scheduler import schedule_tasks


def menu():
    print("\n1. Add Task")
    print("2. Generate Schedule")
    print("3. Mark Task Complete")
    print("4. Exit")


if __name__ == "__main__":
    init_db()

    while True:
        menu()
        choice = input("Select option: ")

        if choice == "1":
            title = input("Title: ")
            est = float(input("Estimated duration (hours): "))
            deadline_days = float(input("Deadline in days: "))
            value = float(input("Value score (1-10): "))
            difficulty = float(input("Difficulty (1-10): "))

            add_task(title, est, deadline_days, value, difficulty)
            print("Task added.")

        elif choice == "2":
            available = float(input("Available time today (hours): "))
            tasks = get_pending_tasks()

            if not tasks:
                print("No pending tasks.")
                continue

            schedule = schedule_tasks(tasks, available)

            print("\nOptimal Schedule:")
            for t in schedule:
                print(f"- {t['title']} (ID: {t['id']})")

        elif choice == "3":
            task_id = int(input("Task ID to mark complete: "))
            actual = float(input("Actual duration (hours): "))

            tasks = get_pending_tasks()
            task = next((t for t in tasks if t["id"] == task_id), None)

            if task:
                complete_task(task, actual)
                print("Task logged and marked complete.")
            else:
                print("Task not found.")

        elif choice == "4":
            break
