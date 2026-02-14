import numpy as np
import pandas as pd


DAILY_WORK_HOURS = 6


def generate_synthetic_samples(n=1000):
    data = []

    for _ in range(n):
        remaining_hours = np.random.uniform(5, 300)
        days_remaining = np.random.uniform(5, 180)

        required_daily = remaining_hours / days_remaining

        # simulate velocity variability
        velocity_noise = np.random.uniform(0.2, 1.5)
        actual_velocity = required_daily * velocity_noise

        # forecasting logic
        if actual_velocity <= 0:
            forecast = 2
        else:
            projected_days = remaining_hours / actual_velocity

            if projected_days > days_remaining:
                forecast = 2  # WILL MISS
            elif projected_days > days_remaining * 0.8:
                forecast = 1  # AT RISK
            else:
                forecast = 0  # SAFE

        velocity_gap = required_daily - actual_velocity
        remaining_ratio = remaining_hours / (remaining_hours + 1)
        workload_pressure = required_daily / DAILY_WORK_HOURS
        allocation_ratio = required_daily / DAILY_WORK_HOURS

        data.append([
            remaining_hours,
            days_remaining,
            required_daily,
            actual_velocity,
            velocity_gap,
            remaining_ratio,
            workload_pressure,
            allocation_ratio,
            forecast
        ])

    columns = [
        "remaining_hours",
        "days_remaining",
        "required_daily",
        "actual_velocity",
        "velocity_gap",
        "remaining_ratio",
        "workload_pressure",
        "allocation_ratio",
        "forecast_label"
    ]

    df = pd.DataFrame(data, columns=columns)
    return df


if __name__ == "__main__":
    df = generate_synthetic_samples(1000)

    print("Sample synthetic data:")
    print(df.head())

    print("\nClass distribution:")
    print(df["forecast_label"].value_counts())
