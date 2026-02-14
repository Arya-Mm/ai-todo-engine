import sqlite3
import pandas as pd

DB_NAME = "tasks.db"


def load_plan_logs():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM plan_logs", conn)
    conn.close()
    return df


def engineer_features():
    df = load_plan_logs()

    if df.empty:
        print("No data available.")
        return None, None

    # Derived features
    df["velocity_gap"] = df["required_daily"] - df["actual_velocity"]
    df["remaining_ratio"] = df["remaining_hours"] / (
        df["remaining_hours"] + 1
    )  # scaled
    df["workload_pressure"] = df["required_daily"] / 6  # relative to max day
    df["allocation_ratio"] = df["allocated_today"] / 6

    # Encode forecast label
    label_map = {
        "SAFE": 0,
        "⚠ AT RISK": 1,
        "🚨 WILL MISS DEADLINE": 2,
        "INSUFFICIENT DATA": -1
    }

    df["forecast_label"] = df["forecast"].map(label_map)

    # Drop rows without usable labels
    df = df[df["forecast_label"] >= 0]

    feature_columns = [
        "remaining_hours",
        "days_remaining",
        "required_daily",
        "actual_velocity",
        "velocity_gap",
        "remaining_ratio",
        "workload_pressure",
        "allocation_ratio"
    ]

    X = df[feature_columns]
    y = df["forecast_label"]

    return X, y


if __name__ == "__main__":
    X, y = engineer_features()

    if X is not None:
        print("\nFeature Sample:")
        print(X.head())

        print("\nLabel Sample:")
        print(y.head())
