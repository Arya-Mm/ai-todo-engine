import sqlite3
from datetime import datetime, timedelta

DB_NAME = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        total_hours REAL,
        deadline DATETIME,
        completed INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        hours_logged REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def add_task(title, total_hours, deadline_days):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    deadline_date = datetime.now() + timedelta(days=deadline_days)

    c.execute("""
    INSERT INTO tasks (title, total_hours, deadline)
    VALUES (?, ?, ?)
    """, (title, total_hours, deadline_date.isoformat()))

    conn.commit()
    conn.close()


def get_tasks():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT id, title, total_hours, deadline
    FROM tasks
    WHERE completed = 0
    """)

    tasks = c.fetchall()
    conn.close()

    result = []
    for t in tasks:
        result.append({
            "id": t[0],
            "title": t[1],
            "total_hours": t[2],
            "deadline": t[3],
        })

    return result


def get_logged_hours(task_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT SUM(hours_logged) FROM logs WHERE task_id = ?", (task_id,))
    total = c.fetchone()[0]

    conn.close()

    return total if total else 0


def log_work(task_id, hours):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (task_id, hours_logged)
    VALUES (?, ?)
    """, (task_id, hours))

    conn.commit()
    conn.close()
