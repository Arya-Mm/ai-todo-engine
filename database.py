import sqlite3
from datetime import datetime

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
        total_hours REAL,
        predicted_completion DATETIME,
        actual_completion DATETIME,
        estimation_error_days REAL
    )
    """)

    # ---------------- Dependencies ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS milestone_dependencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER,
        depends_on_id INTEGER
    )
    """)

    # ---------------- Execution Units ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS execution_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        milestone_id INTEGER,
        estimated_hours REAL,
        completed INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

    conn.commit()
    conn.close()


# ==================================================
# EXECUTION UNIT ENGINE (DYNAMIC CHUNK RESIZING)
# ==================================================

def generate_execution_units(milestone_id, remaining_hours, adaptive_capacity, phase):

    MIN_CHUNK = 0.5
    MAX_CHUNK = 4

    if phase == "SURGE":
        multiplier = 0.6
    elif phase == "COLLAPSE":
        multiplier = 0.25
    else:  # STABLE
        multiplier = 0.4

    optimal_chunk = adaptive_capacity * multiplier
    chunk_size = max(MIN_CHUNK, min(MAX_CHUNK, optimal_chunk))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    while remaining_hours > 0:
        size = min(chunk_size, remaining_hours)

        c.execute("""
        INSERT INTO execution_units (milestone_id, estimated_hours)
        VALUES (?, ?)
        """, (milestone_id, size))

        remaining_hours -= size

    conn.commit()
    conn.close()


def get_pending_units(milestone_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT id, estimated_hours
    FROM execution_units
    WHERE milestone_id = ?
    AND completed = 0
    ORDER BY id ASC
    """, (milestone_id,))

    rows = c.fetchall()
    conn.close()

    return [{"id": r[0], "hours": r[1]} for r in rows]


def mark_unit_completed(unit_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    UPDATE execution_units
    SET completed = 1
    WHERE id = ?
    """, (unit_id,))

    conn.commit()
    conn.close()


# ==================================================
# ESTIMATION TRACKING
# ==================================================

def update_predicted_completion(milestone_id, predicted_date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    UPDATE milestones
    SET predicted_completion = ?
    WHERE id = ?
    """, (predicted_date, milestone_id))

    conn.commit()
    conn.close()


def mark_milestone_completed(milestone_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT predicted_completion
    FROM milestones
    WHERE id = ?
    """, (milestone_id,))

    row = c.fetchone()
    predicted = row[0] if row else None

    actual = datetime.now()
    error_days = 0

    if predicted:
        predicted_dt = datetime.fromisoformat(predicted)
        error_days = (actual - predicted_dt).days

    c.execute("""
    UPDATE milestones
    SET actual_completion = ?, estimation_error_days = ?
    WHERE id = ?
    """, (actual.isoformat(), error_days, milestone_id))

    conn.commit()
    conn.close()


# ==================================================
# DAILY CLOSE LOOP
# ==================================================

def write_daily_summary(adaptive_capacity):

    today = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    SELECT SUM(allocated_today)
    FROM plan_logs
    WHERE DATE(timestamp) = DATE('now')
    """)
    total_allocated = c.fetchone()[0] or 0

    c.execute("""
    SELECT SUM(hours_logged)
    FROM logs
    WHERE DATE(timestamp) = DATE('now')
    """)
    total_logged = c.fetchone()[0] or 0

    performance_ratio = (
        total_logged / total_allocated
        if total_allocated > 0 else 0
    )

    overload_flag = 1 if total_allocated > adaptive_capacity else 0

    c.execute("""
    INSERT INTO daily_summary
    (date, total_allocated, total_logged, performance_ratio, overload_flag)
    VALUES (?, ?, ?, ?, ?)
    """, (today, total_allocated, total_logged, performance_ratio, overload_flag))

    conn.commit()
    conn.close()