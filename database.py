import sqlite3
from datetime import datetime, timedelta

DB_NAME = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Goals
    c.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        deadline DATETIME
    )
    """)

    # Milestones (belong to goals)
    c.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER,
        title TEXT,
        total_hours REAL
    )
    """)

    # Work logs
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER,
        hours_logged REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


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

    goals = []
    for r in rows:
        goals.append({
            "id": r[0],
            "title": r[1],
            "deadline": r[2]
        })

    return goals


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

    milestones = []
    for r in rows:
        milestones.append({
            "id": r[0],
            "title": r[1],
            "total_hours": r[2],
            "deadline": r[3]
        })

    return milestones


def get_logged_hours(milestone_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT SUM(hours_logged) FROM logs WHERE milestone_id = ?", (milestone_id,))
    total = c.fetchone()[0]

    conn.close()
    return total if total else 0


def log_work(milestone_id, hours):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (milestone_id, hours_logged)
    VALUES (?, ?)
    """, (milestone_id, hours))

    conn.commit()
    conn.close()
