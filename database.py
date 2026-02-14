import sqlite3

DB_NAME = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    est_duration REAL,
    deadline_hours REAL,
    value_score REAL,
    difficulty REAL,
    energy_required REAL,
    user_energy REAL,
    available_time REAL,
    completed INTEGER,
    actual_duration REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")


    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        completed INTEGER,
        actual_duration REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
def add_task(title, est_duration, deadline_hours, value_score, difficulty, energy_required):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    INSERT INTO tasks (title, est_duration, deadline_hours, value_score, difficulty, energy_required)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (title, est_duration, deadline_hours, value_score, difficulty, energy_required))



    conn.commit()
    conn.close()
def get_pending_tasks():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT id, title, est_duration, deadline_hours, value_score, difficulty, energy_required FROM tasks WHERE completed = 0")
    rows = c.fetchall()

    conn.close()

    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "title": r[1],
            "est_duration": r[2],
            "deadline_hours": r[3],
            "value_score": r[4],
            "difficulty": r[5],
            "energy_required": r[6],
        })

    return tasks
def complete_task(task, user_energy, available_time, actual_duration):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task["id"],))

    c.execute("""
    INSERT INTO logs (
        task_id,
        est_duration,
        deadline_hours,
        value_score,
        difficulty,
        energy_required,
        user_energy,
        available_time,
        completed,
        actual_duration
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task["id"],
        task["est_duration"],
        task["deadline_hours"],
        task["value_score"],
        task["difficulty"],
        task["energy_required"],
        user_energy,
        available_time,
        1,
        actual_duration
    ))

    conn.commit()
    conn.close()


    conn.commit()
    conn.close()

