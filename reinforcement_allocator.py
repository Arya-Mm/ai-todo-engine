import sqlite3
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor

DB_NAME = "tasks.db"
MODEL_PATH = "allocation_policy.pkl"


def fetch_reward_data():
    conn = sqlite3.connect(DB_NAME)

    df = pd.read_sql_query("""
    SELECT
        remaining_hours,
        days_remaining,
        required_daily,
        actual_velocity,
        allocated_today,
        reward
    FROM plan_logs
    WHERE reward IS NOT NULL
    """, conn)

    conn.close()
    return df


def train_policy():
    df = fetch_reward_data()

    if len(df) < 50:
        print("Not enough reward data to train policy.")
        return None

    X = df[[
        "remaining_hours",
        "days_remaining",
        "required_daily",
        "actual_velocity",
        "allocated_today"
    ]]

    y = df["reward"]

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        random_state=42
    )

    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)

    print("Reinforcement allocation policy trained.")
    return model


def load_policy():
    try:
        return joblib.load(MODEL_PATH)
    except:
        return None


def choose_allocation(state, max_capacity):
    model = load_policy()
    if model is None:
        return None

    remaining, days_remaining, required_daily, actual_velocity = state

    candidates = np.linspace(0.5, max_capacity, 10)

    best_score = -999
    best_alloc = required_daily

    for alloc in candidates:
        feature = np.array([[
            remaining,
            days_remaining,
            required_daily,
            actual_velocity,
            alloc
        ]])

        predicted_reward = model.predict(feature)[0]

        if predicted_reward > best_score:
            best_score = predicted_reward
            best_alloc = alloc

    return round(min(best_alloc, remaining, max_capacity), 2)
