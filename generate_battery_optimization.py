#!/usr/bin/env python3
"""
Generate Battery Optimization Chart for ERCOT
This script creates the battery optimization visualization from notebook 02
"""
import os
import pandas as pd
import numpy as np
from google.cloud import bigquery
import cvxpy as cp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_battery_optimization():
    """Generate battery optimization analysis and visualization"""
    
    # Setup
    PROJECT = os.environ["GCP_PROJECT"]
    DATASET = os.environ.get("BQ_DATASET", "energy_ercot")
    client = bigquery.Client(project=PROJECT)
    
    print("🔍 Loading forecast data from BigQuery...")
    
    # Load forecast from BigQuery
    fc = client.query(f"""
      SELECT timestamp_hour, yhat AS price
      FROM `{PROJECT}.{DATASET}.gold_forecasts`
      WHERE timestamp_hour >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), HOUR)
      ORDER BY timestamp_hour
    """).to_dataframe()
    
    p = fc["price"].to_numpy()
    T = len(p)
    
    print(f"✅ Loaded {T} forecast points")
    print(f"📈 Price range: ${p.min():.2f} - ${p.max():.2f}")
    
    # Battery parameters (adjusted for realistic values)
    S_max, P_max, eta_c, eta_d, lam = 100.0, 50.0, 0.95, 0.95, 0.01
    
    print("🔋 Setting up battery optimization problem...")
    
    # Optimization variables
    c = cp.Variable(T, nonneg=True)  # Charge power
    d = cp.Variable(T, nonneg=True)  # Discharge power  
    b = cp.Variable(T, nonneg=True)  # Bid power
    s = cp.Variable(T+1)              # State of charge
    
    # Constraints
    cons = [s[0] == 0.5*S_max]  # Start at 50% SOC
    
    for t in range(T):
        cons += [s[t+1] == s[t] + eta_c*c[t] - d[t]/eta_d,  # SOC dynamics
                 c[t] <= P_max,                             # Charge limit
                 d[t] <= P_max]                             # Discharge limit
    
    cons += [s >= 0, s <= S_max]  # SOC bounds
    
    # Objective: maximize profit
    obj = cp.Maximize(p@d - p@c + p@b - lam*cp.sum_squares(b))
    
    print("⚙️ Solving optimization problem...")
    
    # Solve with fallback solvers
    prob = cp.Problem(obj, cons)
    try:
        prob.solve(solver=cp.ECOS)
    except:
        try:
            prob.solve(solver=cp.OSQP)
        except:
            prob.solve()
    
    status = prob.status
    value = prob.value
    
    print(f"✅ Optimization status: {status}")
    if value is not None:
        print(f"💰 Optimal objective value: {value:.2f}")
    else:
        print("💰 Optimization value: Not available")
    
    # Prepare optimization results
    out = fc.copy()
    
    # Check if optimization was successful
    if status == "optimal" and c.value is not None:
        out["charge_mwh"] = np.maximum(c.value, 0)
        out["discharge_mwh"] = np.maximum(d.value, 0)
        out["soc_mwh"] = np.maximum(s.value[1:], 0)
        out["bid_mwh"] = np.maximum(b.value, 0)
        # Calculate profit as a scalar value
        profit = float((p*(out["discharge_mwh"]-out["charge_mwh"]+out["bid_mwh"])).sum())
        out["expected_profit"] = profit
    else:
        print("⚠️ Optimization failed, using zero values")
        out["charge_mwh"] = np.zeros(T)
        out["discharge_mwh"] = np.zeros(T)
        out["soc_mwh"] = np.full(T, S_max * 0.5)  # Stay at 50% SOC
        out["bid_mwh"] = np.zeros(T)
        profit = 0.0
        out["expected_profit"] = profit
    
    print("📊 Optimization Results Summary:")
    print(f"   - Total Charge: {out['charge_mwh'].sum():.2f} MWh")
    print(f"   - Total Discharge: {out['discharge_mwh'].sum():.2f} MWh")
    print(f"   - Max SOC: {out['soc_mwh'].max():.2f} MWh")
    print(f"   - Min SOC: {out['soc_mwh'].min():.2f} MWh")
    print(f"   - Expected Profit: ${profit:,.2f}")
    
    # Create battery optimization visualization (before dropping price column)
    print("📈 Creating battery optimization chart...")
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    
    # Plot 1: Price signal
    ax1.plot(out['timestamp_hour'], out['price'], 
             color='blue', linewidth=2, label='Price Signal')
    ax1.set_ylabel('Price ($/MWh)')
    ax1.set_title('Battery Optimization Results - Price Signal & Dispatch', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Charge/Discharge operations
    ax2.bar(out['timestamp_hour'], out['charge_mwh'], 
            color='green', alpha=0.7, label='Charge', width=0.8)
    ax2.bar(out['timestamp_hour'], -out['discharge_mwh'], 
            color='red', alpha=0.7, label='Discharge', width=0.8)
    ax2.set_ylabel('Power (MW)')
    ax2.set_title('Charge/Discharge Operations')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # Plot 3: State of Charge
    ax3.plot(out['timestamp_hour'], out['soc_mwh'], 
             color='purple', linewidth=2, marker='o', markersize=4, label='SOC')
    ax3.fill_between(out['timestamp_hour'], 0, out['soc_mwh'], 
                     alpha=0.3, color='purple')
    ax3.set_ylabel('SOC (MWh)')
    ax3.set_xlabel('Time')
    ax3.set_title('Battery State of Charge')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, S_max * 1.1)
    
    # Format x-axis
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
    ax3.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig('battery_optimization_chart.png', dpi=300, bbox_inches='tight')
    print("💾 Battery optimization chart saved as 'battery_optimization_chart.png'")
    
    plt.show()
    
    # Write results to BigQuery (price column now included in table schema)
    print("💾 Writing optimization results to BigQuery...")
    client.load_table_from_dataframe(out, f"{PROJECT}.{DATASET}.gold_optimizer_outputs").result()
    print("✅ Optimization results saved to gold_optimizer_outputs table")
    
    print("🔋 Battery optimization analysis complete!")
    print("💡 Key insights:")
    print(f"   - Battery charges when prices are low")
    print(f"   - Battery discharges when prices are high") 
    print(f"   - SOC stays within bounds (0 to {S_max} MWh)")
    print(f"   - Total profit: ${profit:,.2f}")
    
    return out

if __name__ == "__main__":
    generate_battery_optimization()
