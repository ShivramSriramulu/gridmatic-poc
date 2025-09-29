#!/usr/bin/env python3
"""
Gridmatic ERCOT POC - Exploratory Data Analysis
Run EDA queries and create visualizations
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
import numpy as np
from datetime import datetime, timedelta

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "energy_ercot")

def run_eda_queries():
    """Run comprehensive EDA queries on BigQuery"""
    client = bigquery.Client(project=PROJECT)
    
    print("🔍 Running Exploratory Data Analysis...")
    
    # 1. Data Overview
    print("\n📊 1. DATA OVERVIEW")
    overview_query = f"""
    SELECT 
      'bronze_ercot' as table_name,
      COUNT(*) as row_count,
      MIN(timestamp_hour) as earliest_data,
      MAX(timestamp_hour) as latest_data,
      COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
    FROM `{PROJECT}.{DATASET}.bronze_ercot`
    UNION ALL
    SELECT 
      'bronze_weather' as table_name,
      COUNT(*) as row_count,
      MIN(timestamp_hour) as earliest_data,
      MAX(timestamp_hour) as latest_data,
      COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
    FROM `{PROJECT}.{DATASET}.bronze_weather`
    UNION ALL
    SELECT 
      'silver_ercot_weather' as table_name,
      COUNT(*) as row_count,
      MIN(timestamp_hour) as earliest_data,
      MAX(timestamp_hour) as latest_data,
      COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
    FROM `{PROJECT}.{DATASET}.silver_ercot_weather`
    """
    
    overview_df = client.query(overview_query).to_dataframe()
    print(overview_df)
    
    # 2. Demand Patterns
    print("\n⚡ 2. DEMAND PATTERNS")
    demand_query = f"""
    SELECT 
      EXTRACT(HOUR FROM timestamp_hour) as hour_of_day,
      AVG(demand_mw) as avg_demand_mw,
      MIN(demand_mw) as min_demand_mw,
      MAX(demand_mw) as max_demand_mw,
      COUNT(*) as sample_count
    FROM `{PROJECT}.{DATASET}.bronze_ercot`
    WHERE demand_mw IS NOT NULL
    GROUP BY EXTRACT(HOUR FROM timestamp_hour)
    ORDER BY hour_of_day
    """
    
    demand_df = client.query(demand_query).to_dataframe()
    print(demand_df.head(10))
    
    # 3. Weather Correlation
    print("\n🌡️ 3. WEATHER CORRELATION")
    weather_query = f"""
    SELECT 
      DATE(timestamp_hour) as date,
      AVG(temp_celsius) as avg_temp_c,
      AVG(demand_mw) as avg_demand_mw,
      CORR(temp_celsius, demand_mw) as temp_demand_correlation
    FROM `{PROJECT}.{DATASET}.silver_ercot_weather`
    WHERE temp_celsius IS NOT NULL AND demand_mw IS NOT NULL
    GROUP BY DATE(timestamp_hour)
    HAVING COUNT(*) >= 20
    ORDER BY date DESC
    LIMIT 10
    """
    
    weather_df = client.query(weather_query).to_dataframe()
    print(weather_df)
    
    # 4. Optimization Results
    print("\n🔋 4. OPTIMIZATION RESULTS")
    opt_query = f"""
    SELECT 
      SUM(expected_profit) as total_profit,
      AVG(expected_profit) as avg_hourly_profit,
      MAX(expected_profit) as max_hourly_profit,
      MIN(expected_profit) as min_hourly_profit,
      AVG(soc_mwh) as avg_soc_mwh,
      SUM(charge_mwh) as total_charge_mwh,
      SUM(discharge_mwh) as total_discharge_mwh
    FROM `{PROJECT}.{DATASET}.gold_optimizer_outputs`
    """
    
    opt_df = client.query(opt_query).to_dataframe()
    print(opt_df)
    
    return overview_df, demand_df, weather_df, opt_df

def create_visualizations(demand_df, weather_df):
    """Create EDA visualizations"""
    print("\n📈 Creating visualizations...")
    
    # Set up the plotting style
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Gridmatic ERCOT POC - Exploratory Data Analysis', fontsize=16)
    
    # 1. Hourly Demand Pattern
    axes[0, 0].plot(demand_df['hour_of_day'], demand_df['avg_demand_mw'], 
                    marker='o', linewidth=2, markersize=6)
    axes[0, 0].set_title('Average Demand by Hour of Day')
    axes[0, 0].set_xlabel('Hour of Day')
    axes[0, 0].set_ylabel('Demand (MW)')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_xticks(range(0, 24, 2))
    
    # 2. Demand Range by Hour
    axes[0, 1].fill_between(demand_df['hour_of_day'], 
                           demand_df['min_demand_mw'], 
                           demand_df['max_demand_mw'], 
                           alpha=0.3, label='Demand Range')
    axes[0, 1].plot(demand_df['hour_of_day'], demand_df['avg_demand_mw'], 
                    color='red', linewidth=2, label='Average')
    axes[0, 1].set_title('Demand Range by Hour')
    axes[0, 1].set_xlabel('Hour of Day')
    axes[0, 1].set_ylabel('Demand (MW)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Temperature vs Demand Scatter
    if not weather_df.empty and 'temp_demand_correlation' in weather_df.columns:
        axes[1, 0].scatter(weather_df['avg_temp_c'], weather_df['avg_demand_mw'], 
                           alpha=0.6, s=50)
        axes[1, 0].set_title('Temperature vs Demand Correlation')
        axes[1, 0].set_xlabel('Average Temperature (°C)')
        axes[1, 0].set_ylabel('Average Demand (MW)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Add correlation coefficient
        corr = weather_df['temp_demand_correlation'].iloc[0] if len(weather_df) > 0 else 0
        axes[1, 0].text(0.05, 0.95, f'Correlation: {corr:.3f}', 
                       transform=axes[1, 0].transAxes, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # 4. Sample Count by Hour
    axes[1, 1].bar(demand_df['hour_of_day'], demand_df['sample_count'], 
                   alpha=0.7, color='skyblue')
    axes[1, 1].set_title('Data Sample Count by Hour')
    axes[1, 1].set_xlabel('Hour of Day')
    axes[1, 1].set_ylabel('Sample Count')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('ercot_eda_analysis.png', dpi=300, bbox_inches='tight')
    print("📊 Visualization saved as 'ercot_eda_analysis.png'")
    
    return fig

def run_anomaly_detection():
    """Detect anomalies in the data"""
    print("\n🚨 ANOMALY DETECTION")
    client = bigquery.Client(project=PROJECT)
    
    # Outlier detection
    outlier_query = f"""
    WITH demand_stats AS (
      SELECT 
        AVG(demand_mw) as mean_demand,
        STDDEV(demand_mw) as stddev_demand
      FROM `{PROJECT}.{DATASET}.bronze_ercot`
      WHERE demand_mw IS NOT NULL
    )
    SELECT 
      timestamp_hour,
      demand_mw,
      ABS(demand_mw - mean_demand) / stddev_demand as z_score
    FROM `{PROJECT}.{DATASET}.bronze_ercot`, demand_stats
    WHERE demand_mw IS NOT NULL
      AND ABS(demand_mw - mean_demand) / stddev_demand > 3
    ORDER BY z_score DESC
    LIMIT 10
    """
    
    outliers_df = client.query(outlier_query).to_dataframe()
    if not outliers_df.empty:
        print("🔍 Top 10 Demand Outliers (Z-score > 3):")
        print(outliers_df)
    else:
        print("✅ No significant outliers detected")
    
    return outliers_df

def generate_insights(overview_df, demand_df, weather_df, opt_df):
    """Generate business insights from the data"""
    print("\n💡 BUSINESS INSIGHTS")
    
    # Peak demand analysis
    peak_hour = demand_df.loc[demand_df['avg_demand_mw'].idxmax()]
    min_hour = demand_df.loc[demand_df['avg_demand_mw'].idxmin()]
    
    print(f"📈 Peak Demand: {peak_hour['avg_demand_mw']:.0f} MW at hour {peak_hour['hour_of_day']}")
    print(f"📉 Minimum Demand: {min_hour['avg_demand_mw']:.0f} MW at hour {min_hour['hour_of_day']}")
    print(f"📊 Demand Range: {peak_hour['avg_demand_mw'] - min_hour['avg_demand_mw']:.0f} MW")
    
    # Weather correlation
    if not weather_df.empty and 'temp_demand_correlation' in weather_df.columns:
        corr = weather_df['temp_demand_correlation'].iloc[0]
        print(f"🌡️ Temperature-Demand Correlation: {corr:.3f}")
        if abs(corr) > 0.5:
            print("   → Strong correlation detected!")
        elif abs(corr) > 0.3:
            print("   → Moderate correlation detected")
        else:
            print("   → Weak correlation")
    
    # Optimization insights
    if not opt_df.empty:
        total_profit = opt_df['total_profit'].iloc[0]
        avg_soc = opt_df['avg_soc_mwh'].iloc[0]
        print(f"💰 Total Expected Profit: ${total_profit:,.2f}")
        print(f"🔋 Average Battery SOC: {avg_soc:.1f} MWh")
    
    # Data quality
    total_rows = overview_df['row_count'].sum()
    print(f"📊 Total Data Points: {total_rows:,}")
    print(f"📅 Data Span: {overview_df['earliest_data'].min()} to {overview_df['latest_data'].max()}")

def main():
    """Main EDA function"""
    print("🚀 Gridmatic ERCOT POC - Exploratory Data Analysis")
    print("=" * 60)
    
    try:
        # Run EDA queries
        overview_df, demand_df, weather_df, opt_df = run_eda_queries()
        
        # Create visualizations
        fig = create_visualizations(demand_df, weather_df)
        
        # Run anomaly detection
        outliers_df = run_anomaly_detection()
        
        # Generate insights
        generate_insights(overview_df, demand_df, weather_df, opt_df)
        
        print("\n✅ EDA Analysis Complete!")
        print("📁 Files generated:")
        print("   - ercot_eda_analysis.png (visualizations)")
        print("   - eda_queries.sql (SQL queries for BigQuery)")
        
    except Exception as e:
        print(f"❌ Error during EDA analysis: {e}")
        raise

if __name__ == "__main__":
    main()
