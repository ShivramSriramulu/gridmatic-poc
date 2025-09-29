#!/usr/bin/env python3
"""
Simple optimization script for BigQuery
"""
import os
import pandas as pd
import numpy as np
from google.cloud import bigquery
import cvxpy as cp

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "energy_ercot")

def generate_optimization():
    client = bigquery.Client(project=PROJECT)
    
    # Read forecast data
    q = f"""
      SELECT timestamp_hour, yhat AS price
      FROM `{PROJECT}.{DATASET}.gold_forecasts`
      WHERE timestamp_hour >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), HOUR)
      ORDER BY timestamp_hour
      LIMIT 48
    """
    fc = client.query(q).to_dataframe()
    
    if fc.empty:
        print("No forecast data found")
        return
    
    print(f"Loaded {len(fc)} forecast rows")
    
    # Optimization parameters
    S_max = 100.0  # Max storage capacity (MWh)
    P_max = 50.0   # Max charge/discharge power (MW)
    eta_c = 0.95   # Charge efficiency
    eta_d = 0.95   # Discharge efficiency
    lam = 0.01     # Regularization parameter
    
    # Price signal (use forecast as price proxy)
    p = fc["price"].to_numpy()
    T = len(p)
    
    # Optimization variables
    c = cp.Variable(T, nonneg=True)  # Charge power
    d = cp.Variable(T, nonneg=True)  # Discharge power
    b = cp.Variable(T, nonneg=True)  # Bid power
    s = cp.Variable(T+1, nonneg=True)  # State of charge
    
    # Constraints
    cons = [s[0] == 0.5*S_max]  # Start at 50% SOC
    
    for t in range(T):
        # SOC dynamics: s[t+1] = s[t] + eta_c*c[t] - d[t]/eta_d
        cons += [s[t+1] == s[t] + eta_c*c[t] - d[t]/eta_d]
        # Power limits
        cons += [c[t] <= P_max, d[t] <= P_max]
    
    # SOC limits
    cons += [s >= 0, s <= S_max]
    
    # Objective: maximize profit = revenue from discharge - cost of charge + bid revenue - regularization
    obj = cp.Maximize(p @ d - p @ c + p @ b - lam*cp.sum_squares(b))
    
    # Solve
    prob = cp.Problem(obj, cons)
    try:
        prob.solve(solver=cp.OSQP, verbose=True)
    except:
        try:
            prob.solve(solver=cp.SCS, verbose=True)
        except:
            prob.solve(verbose=True)  # Use default solver
    
    if prob.status != cp.OPTIMAL:
        print(f"Optimization failed: {prob.status}")
        return
    
    # Prepare output (only include columns that match table schema)
    out = pd.DataFrame()
    out["timestamp_hour"] = fc["timestamp_hour"]
    out["charge_mwh"] = np.maximum(c.value, 0)
    out["discharge_mwh"] = np.maximum(d.value, 0)
    out["soc_mwh"] = np.maximum(s.value[1:], 0)
    out["bid_mwh"] = np.maximum(b.value, 0)
    
    # Calculate expected profit
    profit = (p * (out["discharge_mwh"] - out["charge_mwh"] + out["bid_mwh"])).sum()
    out["expected_profit"] = profit
    
    print(f"Expected profit: ${profit:.2f}")
    print(f"Max SOC: {out['soc_mwh'].max():.1f} MWh")
    print(f"Total charge: {out['charge_mwh'].sum():.1f} MWh")
    print(f"Total discharge: {out['discharge_mwh'].sum():.1f} MWh")
    
    # Load to gold table
    client.load_table_from_dataframe(out, f"{PROJECT}.{DATASET}.gold_optimizer_outputs").result()
    print(f"Generated optimization with {len(out)} rows")

if __name__ == "__main__":
    generate_optimization()
