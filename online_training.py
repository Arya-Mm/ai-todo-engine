import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

DB_NAME = "tasks.db"
MODEL_PATH = "deadline_risk_model.pkl"


def fetch_training_data():
    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
    SELECT
        remaining_hours,
        days_remaining,
        required_daily,
        actual_velocity,
        allocated_today,
        forecast
    FROM plan_logs
    WHERE forecast IS NOT NULL
    """, conn)

    conn.close()

    return df


def retrain_model():
    df = fetch_training_data()

    if len(df) < 50:
        print("Not enough real data to retrain.")
        return

    X = df[[
        "remaining_hours",
        "days_remaining",
        "required_daily",
        "actual_velocity",
        "allocated_today"
    ]]

    y = df["forecast"]

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42
    )

    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)

    print("Model retrained and updated.")
