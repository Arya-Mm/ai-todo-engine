import sqlite3
from datetime import datetime, timedelta

DB_NAME = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # TASKS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        est_duration REAL,
        deadline DATETIME,
        value_score REAL,
        difficulty REAL,
        completed INTEGER DEFAULT 0
    )
    """)

    # LOGS TABLE (Behavior Dataset)
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        est_duration REAL,
        deadline DATETIME,
        value_score REAL,
        difficulty REAL,
        hour_of_day INTEGER,
        day_of_week INTEGER,
        completed INTEGER,
        actual_duration REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def add_task(title, est_duration, deadline_days, value_score, difficulty):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    deadline_date = datetime.now() + timedelta(days=deadline_days)

    c.execute("""
    INSERT INTO tasks (title, est_duration, deadline, value_score, difficulty)
    VALUES (?, ?, ?, ?, ?)
    """, (title, est_duration, deadline_date.isoformat(), value_score, difficulty))

    conn.commit()
    conn.close()


def get_pending_tasks():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT id, title, est_duration, deadline, value_score, difficulty
    FROM tasks
    WHERE completed = 0
    """)

    rows = c.fetchall()
    conn.close()

    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "title": r[1],
            "est_duration": r[2],
            "deadline": r[3],
            "value_score": r[4],
            "difficulty": r[5],
        })

    return tasks


def complete_task(task, actual_duration):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    now = datetime.now()

    # Mark task complete
    c.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task["id"],))

    # Log behavioral snapshot
    c.execute("""
    INSERT INTO logs (
        task_id,
        est_duration,
        deadline,
        value_score,
        difficulty,
        hour_of_day,
        day_of_week,
        completed,
        actual_duration
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task["id"],
        task["est_duration"],
        task["deadline"],
        task["value_score"],
        task["difficulty"],
        now.hour,
        now.weekday(),
        1,
        actual_duration
    ))

    conn.commit()
    conn.close()
