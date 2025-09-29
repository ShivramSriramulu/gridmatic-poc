# pipeline/flyte/tasks.py
import os
import numpy as np
import pandas as pd
import cvxpy as cp
from flytekit import task
from google.cloud import bigquery
from prophet import Prophet

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "energy_ercot")

# ---- ETL (re-uses your existing ETL functions) ----
@task
def etl_refresh() -> bool:
    # Import here to avoid heavy deps at module import time
    from pipeline import etl_ingest as etl
    etl.ingest_ercot_last_year()
    etl.ingest_weather_last_year()
    etl.build_silver_table()
    return True

# ---- Forecast → gold_forecasts ----
@task
def forecast_to_gold(horizon_hours: int = 48) -> bool:
    client = bigquery.Client(project=PROJECT)
    df = client.query(f"""
        SELECT timestamp_hour, demand_mw
        FROM `{PROJECT}.{DATASET}.silver_ercot_weather`
        WHERE timestamp_hour >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
        ORDER BY timestamp_hour
    """).to_dataframe()

    dfp = df.rename(columns={"timestamp_hour":"ds","demand_mw":"y"})
    m = Prophet(daily_seasonality=True, weekly_seasonality=True)
    m.fit(dfp)

    future = m.make_future_dataframe(periods=horizon_hours, freq="H")
    fc = m.predict(future).tail(horizon_hours)[["ds","yhat","yhat_lower","yhat_upper"]]
    fc = fc.rename(columns={"ds":"timestamp_hour"})

    client.load_table_from_dataframe(
        fc,
        f"{PROJECT}.{DATASET}.gold_forecasts"
    ).result()
    return True

# ---- Optimizer → gold_optimizer_outputs ----
@task
def optimize_to_gold(
    S_max: float = 100.0,   # MWh
    P_max: float = 50.0,    # MW (MWh per hour)
    eta_c: float = 0.95,
    eta_d: float = 0.95,
    lam: float = 0.01
) -> bool:
    client = bigquery.Client(project=PROJECT)
    fc = client.query(f"""
        SELECT timestamp_hour, yhat AS price
        FROM `{PROJECT}.{DATASET}.gold_forecasts`
        WHERE timestamp_hour >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), HOUR)
        ORDER BY timestamp_hour
    """).to_dataframe()

    p = fc["price"].to_numpy()
    T = len(p)

    c = cp.Variable(T, nonneg=True)
    d = cp.Variable(T, nonneg=True)
    b = cp.Variable(T, nonneg=True)  # simple long bid
    s = cp.Variable(T+1)

    cons = [s[0] == 0.5 * S_max]
    for t in range(T):
        cons += [
            s[t+1] == s[t] + eta_c * c[t] - d[t] / eta_d,
            c[t] <= P_max, d[t] <= P_max
        ]
    cons += [s >= 0, s <= S_max]

    obj = cp.Maximize(p @ d - p @ c + p @ b - lam * cp.sum_squares(b))
    cp.Problem(obj, cons).solve(solver=cp.ECOS)

    out = fc.copy()
    out["charge_mwh"]    = np.maximum(c.value, 0)
    out["discharge_mwh"] = np.maximum(d.value, 0)
    out["soc_mwh"]       = np.maximum(s.value[1:], 0)
    out["bid_mwh"]       = np.maximum(b.value, 0)
    out["expected_profit"] = float(
        (p * (out["discharge_mwh"] - out["charge_mwh"] + out["bid_mwh"])).sum()
    )

    client.load_table_from_dataframe(
        out[["timestamp_hour","price","charge_mwh","discharge_mwh","soc_mwh","bid_mwh","expected_profit"]],
        f"{PROJECT}.{DATASET}.gold_optimizer_outputs"
    ).result()
    return True
