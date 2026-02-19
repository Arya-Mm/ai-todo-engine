import sqlite3
from datetime import datetime, timedelta

DB_NAME = "tasks.db"


# ==================================================
# INITIALIZATION
# ==================================================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ---------------- Goals ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        deadline DATETIME
    )
    """)

    # ---------------- Milestones ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER,
        title TEXT,
        total_hours REAL
    )
    """)

    # ---------------- Work Logs ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER,
        hours_logged REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- Plan Logs ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS plan_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER,
        remaining_hours REAL,
        days_remaining INTEGER,
        required_daily REAL,
        actual_velocity REAL,
        allocated_today REAL,
        forecast TEXT,
        reward REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ---------------- Daily Summary ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS daily_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        total_allocated REAL,
        total_logged REAL,
        performance_ratio REAL,
        overload_flag INTEGER
    )
    """)

    # ---------------- RL Transitions ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER,
        state TEXT,
        action REAL,
        reward REAL,
        next_state TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ==================================================
# GOALS & MILESTONES
# ==================================================

def add_goal(title, deadline_days):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    deadline = datetime.now() + timedelta(days=deadline_days)

    c.execute("""
    INSERT INTO goals (title, deadline)
    VALUES (?, ?)
    """, (title, deadline.isoformat()))

    conn.commit()
    conn.close()


def add_milestone(goal_id, title, total_hours):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO milestones (goal_id, title, total_hours)
    VALUES (?, ?, ?)
    """, (goal_id, title, total_hours))

    conn.commit()
    conn.close()


def get_goals():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT id, title, deadline FROM goals")
    rows = c.fetchall()
    conn.close()

    return [{"id": r[0], "title": r[1], "deadline": r[2]} for r in rows]


def get_milestones():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT m.id, m.title, m.total_hours, g.deadline
    FROM milestones m
    JOIN goals g ON m.goal_id = g.id
    """)
    rows = c.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "total_hours": r[2],
            "deadline": r[3]
        }
        for r in rows
    ]


# ==================================================
# WORK LOGGING
# ==================================================

def log_work(milestone_id, hours):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (milestone_id, hours_logged)
    VALUES (?, ?)
    """, (milestone_id, hours))

    conn.commit()
    conn.close()


def get_logged_hours(milestone_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT SUM(hours_logged) FROM logs WHERE milestone_id = ?", (milestone_id,))
    total = c.fetchone()[0]
    conn.close()

    return total if total else 0


def get_recent_velocity(milestone_id, days=7):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT SUM(hours_logged)
    FROM logs
    WHERE milestone_id = ?
    AND timestamp >= datetime('now', ?)
    """, (milestone_id, f'-{days} days'))

    total = c.fetchone()[0]
    conn.close()

    return (total / days) if total else 0


def get_log_count(milestone_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM logs WHERE milestone_id = ?", (milestone_id,))
    count = c.fetchone()[0]
    conn.close()

    return count


# ==================================================
# PLAN LOGGING
# ==================================================

def log_plan(milestone_id, remaining, days_remaining,
             required_daily, actual_velocity,
             allocated, forecast):

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO plan_logs (
        milestone_id,
        remaining_hours,
        days_remaining,
        required_daily,
        actual_velocity,
        allocated_today,
        forecast,
        reward
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
    """, (
        milestone_id,
        remaining,
        days_remaining,
        required_daily,
        actual_velocity,
        allocated,
        forecast
    ))

    conn.commit()
    conn.close()


def update_plan_reward(plan_log_id, reward):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    UPDATE plan_logs
    SET reward = ?
    WHERE id = ?
    """, (reward, plan_log_id))

    conn.commit()
    conn.close()


def get_last_plan_state(milestone_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT id, required_daily, forecast
    FROM plan_logs
    WHERE milestone_id = ?
    ORDER BY timestamp DESC
    LIMIT 1
    """, (milestone_id,))

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "plan_id": row[0],
        "required_daily": row[1],
        "forecast": row[2]
    }


# ==================================================
# RL TRANSITIONS
# ==================================================

def log_transition(milestone_id, state, action, reward, next_state):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO transitions (
        milestone_id,
        state,
        action,
        reward,
        next_state
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        milestone_id,
        str(state),
        action,
        reward,
        str(next_state)
    ))

    conn.commit()
    conn.close()


# ==================================================
# PERFORMANCE / CAPACITY SUPPORT
# ==================================================

def get_recent_daily_output(days=7):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT DATE(timestamp), SUM(hours_logged)
    FROM logs
    WHERE timestamp >= datetime('now', ?)
    GROUP BY DATE(timestamp)
    """, (f'-{days} days',))

    rows = c.fetchall()
    conn.close()

    if not rows:
        return 0

    total = sum(r[1] for r in rows)
    return total / days


def get_recent_performance(days=7):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT performance_ratio
    FROM daily_summary
    ORDER BY date DESC
    LIMIT ?
    """, (days,))

    rows = c.fetchall()
    conn.close()

    return [r[0] for r in rows]
