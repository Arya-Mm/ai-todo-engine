from datetime import datetime

from database import (
    init_db,
    add_goal,
    add_milestone,
    get_goals,
    get_milestones,
    log_work,
    get_last_plan_state,
    get_logged_hours,
    compute_reward,
    update_plan_reward,
    log_transition
)

from scheduler import generate_operator_briefing, compute_execution_embedding
from td_learning import update_q
from online_training import retrain_model


# --------------------------------------------------
# SAFE INPUT HELPERS
# --------------------------------------------------

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


# --------------------------------------------------
# MENU
# --------------------------------------------------

def menu():
    print("\n1. Add Goal")
    print("2. Add Milestone to Goal")
    print("3. Generate Operator Briefing")
    print("4. Log Work (Triggers Learning)")
    print("5. Retrain Deadline Model")
    print("6. Exit")


# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

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
                print("No goals found.")
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

        # -------- LOG WORK + TD LEARNING --------
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

            # -------- FETCH PREVIOUS PLAN STATE --------
            prev_plan = get_last_plan_state(milestone_id)

            if not prev_plan:
                print("No previous plan found. Generate briefing first.")
                continue

            milestone = next(m for m in milestones if m["id"] == milestone_id)

            # -------- PREVIOUS STATE EMBEDDING --------
            adaptive_capacity = 6  # can replace with dynamic call
            prev_embedding = compute_execution_embedding(
                milestone,
                adaptive_capacity
            )

            # -------- LOG WORK --------
            log_work(milestone_id, hours)

            # -------- NEW STATE --------
            logged = get_logged_hours(milestone_id)
            remaining = milestone["total_hours"] - logged

            deadline = datetime.fromisoformat(milestone["deadline"])
            days_remaining = max((deadline - datetime.now()).days, 1)

            new_required_daily = remaining / days_remaining
            performance_ratio = (
                hours / prev_plan["required_daily"]
                if prev_plan["required_daily"] > 0 else 0
            )

            new_forecast = prev_plan["forecast"]
            completed = remaining <= 0

            # -------- COMPUTE REWARD --------
            reward = compute_reward(
                prev_plan["required_daily"],
                new_required_daily,
                performance_ratio,
                prev_plan["forecast"],
                new_forecast,
                completed
            )

            # -------- UPDATE PLAN LOG --------
            update_plan_reward(prev_plan["plan_id"], reward)

            # -------- NEXT EMBEDDING --------
            next_embedding = compute_execution_embedding(
                milestone,
                adaptive_capacity
            )

            # -------- TD UPDATE --------
            update_q(
                prev_embedding,
                prev_plan["required_daily"],
                reward,
                next_embedding
            )

            # -------- LOG TRANSITION --------
            log_transition(
                milestone_id,
                prev_embedding,
                prev_plan["required_daily"],
                reward,
                next_embedding
            )

            print(f"Work logged.")
            print(f"Reward: {reward}")

        # -------- RETRAIN DEADLINE MODEL --------
        elif choice == "5":
            retrain_model()

        # -------- EXIT --------
        elif choice == "6":
            print("Exiting.")
            break

        else:
            print("Invalid option. Choose 1-6.")
