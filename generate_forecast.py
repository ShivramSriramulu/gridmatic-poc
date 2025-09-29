#!/usr/bin/env python3
"""
Simple forecast generation script for BigQuery
"""
import os
import pandas as pd
from google.cloud import bigquery
from prophet import Prophet

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "energy_ercot")

def generate_forecast():
    client = bigquery.Client(project=PROJECT)
    
    # Read from bronze table directly
    q = f"""
      SELECT timestamp_hour, demand_mw
      FROM `{PROJECT}.{DATASET}.bronze_ercot`
      WHERE demand_mw IS NOT NULL
      ORDER BY timestamp_hour
    """
    df = client.query(q).to_dataframe()
    
    if df.empty:
        print("No data found in bronze_ercot")
        return
    
    print(f"Loaded {len(df)} rows from bronze_ercot")
    
    # Prepare for Prophet (remove timezone)
    dfp = df.rename(columns={"timestamp_hour": "ds", "demand_mw": "y"})
    dfp['ds'] = dfp['ds'].dt.tz_localize(None)  # Remove timezone for Prophet
    
    # Train Prophet model
    m = Prophet(daily_seasonality=True, weekly_seasonality=True)
    m.fit(dfp)
    
    # Generate 48-hour forecast
    future = m.make_future_dataframe(periods=48, freq="h")
    fc = m.predict(future).tail(48)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    fc = fc.rename(columns={"ds": "timestamp_hour"})
    
    # Load to gold table
    client.load_table_from_dataframe(fc, f"{PROJECT}.{DATASET}.gold_forecasts").result()
    print(f"Generated forecast with {len(fc)} rows")

if __name__ == "__main__":
    generate_forecast()
