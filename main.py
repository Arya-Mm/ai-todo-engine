from database import init_db, add_task, get_tasks, log_work
from scheduler import schedule


def menu():
    print("\n1. Add Task")
    print("2. Generate Today's Plan")
    print("3. Log Work")
    print("4. Exit")


if __name__ == "__main__":
    init_db()

    while True:
        menu()
        choice = input("Select option: ")

        if choice == "1":
            title = input("Title: ")
            total_hours = float(input("Total hours required: "))
            deadline_days = float(input("Deadline in days: "))

            add_task(title, total_hours, deadline_days)
            print("Task added.")

        elif choice == "2":
            tasks = get_tasks()
            plan = schedule(tasks)

            print("\nToday's Execution Plan:")
            for task, hours in plan:
                print(f"- {task['title']} → {hours} hrs (ID: {task['id']})")

        elif choice == "3":
            task_id = int(input("Task ID: "))
            hours = float(input("Hours worked: "))
            log_work(task_id, hours)
            print("Work logged.")

        elif choice == "4":
            break
