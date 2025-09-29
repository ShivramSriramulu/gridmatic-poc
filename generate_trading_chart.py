#!/usr/bin/env python3
"""
Generate Trading Chart for ERCOT Forecast
This script creates the trading-style visualization from notebook 01
"""
import os
import pandas as pd
from google.cloud import bigquery
from prophet import Prophet
import matplotlib.pyplot as plt

def generate_trading_chart():
    """Generate the trading chart visualization"""
    
    # Setup
    PROJECT = os.environ["GCP_PROJECT"]
    DATASET = os.environ.get("BQ_DATASET", "energy_ercot")
    client = bigquery.Client(project=PROJECT)
    
    print("🔍 Querying ERCOT demand data...")
    
    # Query BigQuery for ERCOT demand data
    df = client.query(f"""
      SELECT timestamp_hour, demand_mw
      FROM `{PROJECT}.{DATASET}.silver_ercot_weather`
      WHERE timestamp_hour >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
      ORDER BY timestamp_hour
    """).to_dataframe()
    
    print(f"✅ Loaded {len(df)} rows of demand data")
    
    # Prepare data for Prophet
    dfp = df.rename(columns={"timestamp_hour":"ds", "demand_mw":"y"})
    dfp['ds'] = dfp['ds'].dt.tz_localize(None)  # Remove timezone
    
    # Train Prophet model
    print("🤖 Training Prophet model...")
    m = Prophet(daily_seasonality=True, weekly_seasonality=True)
    m.fit(dfp)
    
    # Generate 48-hour forecast
    print("🔮 Generating 48-hour forecast...")
    future = m.make_future_dataframe(periods=48, freq="H")
    fc = m.predict(future)
    fc_48 = fc.tail(48)
    
    print(f"✅ Forecast complete: {len(fc_48)} hours ahead")
    
    # Create the trading chart
    print("📈 Creating trading chart...")
    plt.figure(figsize=(12,4))
    
    # Get recent 7 days of actual data
    recent = dfp.tail(7*24)
    
    # Plot actual demand (last 7 days)
    plt.plot(recent["ds"], recent["y"], 
             label="Actual (Demand)", 
             color='blue', 
             linewidth=1.5)
    
    # Plot forecast (48 hours)
    plt.plot(fc_48["ds"], fc_48["yhat"], 
             label="Forecast (48h)", 
             color='red', 
             linewidth=2)
    
    # Add uncertainty band
    plt.fill_between(fc_48["ds"], 
                     fc_48["yhat_lower"], 
                     fc_48["yhat_upper"], 
                     alpha=0.2, 
                     color='red',
                     label="Uncertainty")
    
    # Formatting
    plt.title("ERCOT Hourly Forecast vs Actual (Trading View)", fontsize=14, fontweight='bold')
    plt.xlabel("Time")
    plt.ylabel("Demand (MW)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Add vertical line to separate actual from forecast
    if len(recent) > 0:
        last_actual = recent["ds"].iloc[-1]
        plt.axvline(x=last_actual, color='gray', linestyle='--', alpha=0.7)
        plt.text(last_actual, plt.ylim()[1]*0.95, 'Now', 
                 rotation=90, ha='right', va='top', fontsize=10)
    
    # Save the chart
    plt.savefig('ercot_trading_chart.png', dpi=300, bbox_inches='tight')
    print("💾 Trading chart saved as 'ercot_trading_chart.png'")
    
    # Show summary stats
    print(f"\n📊 Chart Summary:")
    print(f"   - Actual data: {len(recent)} hours (7 days)")
    print(f"   - Forecast: {len(fc_48)} hours (48 hours)")
    print(f"   - Actual range: {recent['y'].min():.0f} - {recent['y'].max():.0f} MW")
    print(f"   - Forecast range: {fc_48['yhat'].min():.0f} - {fc_48['yhat'].max():.0f} MW")
    
    plt.show()
    
    return df, fc_48

if __name__ == "__main__":
    generate_trading_chart()
