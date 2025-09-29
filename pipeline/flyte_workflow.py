from flytekit import task, workflow, Resources
from flytekit.types.file import PythonFile
import os
import pandas as pd
from google.cloud import bigquery
from prophet import Prophet
import cvxpy as cp
import numpy as np
from datetime import datetime

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "energy_ercot")

@task(
    requests=Resources(cpu="1", mem="2Gi"),
    limits=Resources(cpu="2", mem="4Gi")
)
def etl_refresh() -> str:
    """
    Task 1: Refresh ETL pipeline and rebuild silver table
    """
    print(f"[{datetime.now()}] Starting ETL refresh...")
    
    try:
        # Import and run ETL pipeline
        import pipeline.etl_ingest as etl
        
        # Ingest fresh ERCOT data
        print("Ingesting ERCOT data...")
        etl.ingest_ercot_last_year()
        
        # Ingest fresh weather data
        print("Ingesting weather data...")
        etl.ingest_weather_last_year()
        
        # Build/refresh silver table
        print("Building silver table...")
        etl.build_silver_table()
        
        print(f"[{datetime.now()}] ETL refresh completed successfully")
        return "ETL refresh completed"
        
    except Exception as e:
        error_msg = f"ETL refresh failed: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

@task(
    requests=Resources(cpu="2", mem="4Gi"),
    limits=Resources(cpu="4", mem="8Gi")
)
def forecast_to_gold(horizon_hours: int = 48) -> str:
    """
    Task 2: Generate Prophet forecasts and write to gold_forecasts
    """
    print(f"[{datetime.now()}] Starting forecast generation...")
    
    try:
        client = bigquery.Client(project=PROJECT)
        
        # Query historical data for training
        q = f"""
          SELECT timestamp_hour, demand_mw
          FROM `{PROJECT}.{DATASET}.silver_ercot_weather`
          WHERE timestamp_hour >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
            AND demand_mw IS NOT NULL
          ORDER BY timestamp_hour
        """
        
        print("Loading historical data for Prophet training...")
        df = client.query(q).to_dataframe()
        
        if df.empty:
            raise Exception("No historical data found for forecasting")
        
        print(f"Loaded {len(df)} historical data points")
        
        # Prepare data for Prophet (remove timezone)
        dfp = df.rename(columns={"timestamp_hour": "ds", "demand_mw": "y"})
        dfp['ds'] = dfp['ds'].dt.tz_localize(None)
        
        # Train Prophet model
        print("Training Prophet model...")
        m = Prophet(
            daily_seasonality=True, 
            weekly_seasonality=True,
            yearly_seasonality=True
        )
        m.fit(dfp)
        
        # Generate forecast
        print(f"Generating {horizon_hours}-hour forecast...")
        future = m.make_future_dataframe(periods=horizon_hours, freq="H")
        fc = m.predict(future).tail(horizon_hours)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        fc = fc.rename(columns={"ds": "timestamp_hour"})
        
        # Write to BigQuery
        print("Writing forecast to gold_forecasts...")
        client.load_table_from_dataframe(fc, f"{PROJECT}.{DATASET}.gold_forecasts").result()
        
        print(f"[{datetime.now()}] Forecast generation completed - {len(fc)} hours")
        return f"Forecast completed - {len(fc)} hours"
        
    except Exception as e:
        error_msg = f"Forecast generation failed: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

@task(
    requests=Resources(cpu="2", mem="4Gi"),
    limits=Resources(cpu="4", mem="8Gi")
)
def optimize_to_gold(S_max: float = 100.0, P_max: float = 50.0, eta_c: float = 0.95, eta_d: float = 0.95, lam: float = 0.01) -> str:
    """
    Task 3: Run battery optimization and write to gold_optimizer_outputs
    """
    print(f"[{datetime.now()}] Starting battery optimization...")
    
    try:
        client = bigquery.Client(project=PROJECT)
        
        # Query forecast data for optimization
        q = f"""
          SELECT timestamp_hour, yhat AS price
          FROM `{PROJECT}.{DATASET}.gold_forecasts`
          WHERE timestamp_hour >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), HOUR)
          ORDER BY timestamp_hour
        """
        
        print("Loading forecast data for optimization...")
        fc = client.query(q).to_dataframe()
        
        if fc.empty:
            raise Exception("No forecast data found for optimization")
        
        print(f"Loaded {len(fc)} forecast points")
        
        p = fc["price"].to_numpy()
        T = len(p)
        
        print(f"Optimization parameters: S_max={S_max}, P_max={P_max}, eta_c={eta_c}, eta_d={eta_d}")
        
        # Optimization variables
        c = cp.Variable(T, nonneg=True)  # Charge power
        d = cp.Variable(T, nonneg=True)   # Discharge power
        b = cp.Variable(T, nonneg=True)   # Bid power
        s = cp.Variable(T+1)              # State of charge
        
        # Constraints
        cons = [s[0] == 0.5*S_max]  # Start at 50% SOC
        
        for t in range(T):
            cons += [
                s[t+1] == s[t] + eta_c*c[t] - d[t]/eta_d,  # SOC dynamics
                c[t] <= P_max,                             # Charge limit
                d[t] <= P_max                              # Discharge limit
            ]
        
        cons += [s >= 0, s <= S_max]  # SOC bounds
        
        # Objective: maximize profit
        obj = cp.Maximize(p @ d - p @ c + p @ b - lam*cp.sum_squares(b))
        
        # Solve optimization
        print("Solving optimization problem...")
        prob = cp.Problem(obj, cons)
        
        # Try multiple solvers
        try:
            prob.solve(solver=cp.ECOS)
        except:
            try:
                prob.solve(solver=cp.OSQP)
            except:
                prob.solve()
        
        if prob.status != "optimal":
            raise Exception(f"Optimization failed with status: {prob.status}")
        
        # Prepare results
        out = fc.copy()
        out["charge_mwh"] = np.maximum(c.value, 0)
        out["discharge_mwh"] = np.maximum(d.value, 0)
        out["soc_mwh"] = np.maximum(s.value[1:], 0)
        out["bid_mwh"] = np.maximum(b.value, 0)
        
        # Calculate profit
        profit = float((p * (out["discharge_mwh"] - out["charge_mwh"] + out["bid_mwh"])).sum())
        out["expected_profit"] = profit
        
        # Write to BigQuery
        print("Writing optimization results to gold_optimizer_outputs...")
        client.load_table_from_dataframe(out, f"{PROJECT}.{DATASET}.gold_optimizer_outputs").result()
        
        print(f"[{datetime.now()}] Optimization completed - Profit: ${profit:,.2f}")
        return f"Optimization completed - Profit: ${profit:,.2f}"
        
    except Exception as e:
        error_msg = f"Optimization failed: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

@workflow
def nightly_workflow():
    """
    Nightly automation workflow:
    Task 1 → ETL (refresh silver)
    Task 2 → Forecast (write gold_forecasts)  
    Task 3 → Optimizer (write gold_optimizer_outputs)
    """
    print(f"[{datetime.now()}] Starting nightly workflow...")
    
    # Sequential execution for data dependencies
    etl_result = etl_refresh()
    forecast_result = forecast_to_gold()
    optimizer_result = optimize_to_gold()
    
    print(f"[{datetime.now()}] Nightly workflow completed successfully")
    return {
        "etl": etl_result,
        "forecast": forecast_result, 
        "optimizer": optimizer_result
    }
