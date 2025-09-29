# Gridmatic ERCOT POC - EDA Queries for BigQuery

## 🚀 Quick Start EDA Queries

Here are the most useful EDA queries you can run directly in BigQuery to explore your ERCOT energy data:

### 1. **Data Overview & Quality**
```sql
-- Check data availability across all tables
SELECT 
  'bronze_ercot' as table_name,
  COUNT(*) as row_count,
  MIN(timestamp_hour) as earliest_data,
  MAX(timestamp_hour) as latest_data,
  COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
UNION ALL
SELECT 
  'bronze_weather' as table_name,
  COUNT(*) as row_count,
  MIN(timestamp_hour) as earliest_data,
  MAX(timestamp_hour) as latest_data,
  COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
FROM `gridmatic-473617.energy_ercot.bronze_weather`
UNION ALL
SELECT 
  'silver_ercot_weather' as table_name,
  COUNT(*) as row_count,
  MIN(timestamp_hour) as earliest_data,
  MAX(timestamp_hour) as latest_data,
  COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
FROM `gridmatic-473617.energy_ercot.silver_ercot_weather`;
```

### 2. **Demand Patterns Analysis**
```sql
-- Hourly demand patterns (peak/off-peak analysis)
SELECT 
  EXTRACT(HOUR FROM timestamp_hour) as hour_of_day,
  AVG(demand_mw) as avg_demand_mw,
  MIN(demand_mw) as min_demand_mw,
  MAX(demand_mw) as max_demand_mw,
  COUNT(*) as sample_count
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY EXTRACT(HOUR FROM timestamp_hour)
ORDER BY hour_of_day;
```

### 3. **Weather Correlation**
```sql
-- Temperature vs Demand correlation
SELECT 
  DATE(timestamp_hour) as date,
  AVG(temp_celsius) as avg_temp_c,
  AVG(demand_mw) as avg_demand_mw,
  CORR(temp_celsius, demand_mw) as temp_demand_correlation
FROM `gridmatic-473617.energy_ercot.silver_ercot_weather`
WHERE temp_celsius IS NOT NULL AND demand_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
HAVING COUNT(*) >= 20
ORDER BY date DESC
LIMIT 30;
```

### 4. **Peak Demand Analysis**
```sql
-- Top 20 peak demand days
SELECT 
  DATE(timestamp_hour) as date,
  MAX(demand_mw) as peak_demand_mw,
  EXTRACT(HOUR FROM timestamp_hour) as peak_hour
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
ORDER BY peak_demand_mw DESC
LIMIT 20;
```

### 5. **Optimization Results**
```sql
-- Battery operation summary
SELECT 
  DATE(timestamp_hour) as date,
  SUM(charge_mwh) as total_charge_mwh,
  SUM(discharge_mwh) as total_discharge_mwh,
  AVG(soc_mwh) as avg_soc_mwh,
  MAX(soc_mwh) as max_soc_mwh,
  MIN(soc_mwh) as min_soc_mwh,
  SUM(expected_profit) as daily_profit
FROM `gridmatic-473617.energy_ercot.gold_optimizer_outputs`
GROUP BY DATE(timestamp_hour)
ORDER BY date DESC;
```

### 6. **Anomaly Detection**
```sql
-- Demand outliers (Z-score > 3)
WITH demand_stats AS (
  SELECT 
    AVG(demand_mw) as mean_demand,
    STDDEV(demand_mw) as stddev_demand
  FROM `gridmatic-473617.energy_ercot.bronze_ercot`
  WHERE demand_mw IS NOT NULL
)
SELECT 
  timestamp_hour,
  demand_mw,
  ABS(demand_mw - mean_demand) / stddev_demand as z_score
FROM `gridmatic-473617.energy_ercot.bronze_ercot`, demand_stats
WHERE demand_mw IS NOT NULL
  AND ABS(demand_mw - mean_demand) / stddev_demand > 3
ORDER BY z_score DESC
LIMIT 20;
```

### 7. **Trading Opportunities**
```sql
-- High volatility days (trading opportunities)
SELECT 
  DATE(timestamp_hour) as date,
  MIN(demand_mw) as min_demand,
  MAX(demand_mw) as max_demand,
  MAX(demand_mw) - MIN(demand_mw) as daily_range,
  STDDEV(demand_mw) as daily_volatility,
  COUNT(*) as hourly_readings
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
HAVING COUNT(*) >= 20
ORDER BY daily_range DESC
LIMIT 20;
```

### 8. **Forecast Analysis**
```sql
-- Forecast accuracy and uncertainty
SELECT 
  DATE(timestamp_hour) as forecast_date,
  AVG(yhat) as avg_forecast_mw,
  AVG(yhat_lower) as avg_lower_bound,
  AVG(yhat_upper) as avg_upper_bound,
  AVG(yhat_upper - yhat_lower) as avg_confidence_interval,
  COUNT(*) as forecast_points
FROM `gridmatic-473617.energy_ercot.gold_forecasts`
GROUP BY DATE(timestamp_hour)
ORDER BY forecast_date DESC
LIMIT 10;
```

## 📊 Key Insights to Look For

### **Demand Patterns**
- **Peak Hours**: Usually 6-9 AM and 6-9 PM
- **Off-Peak**: Late night/early morning (2-5 AM)
- **Weekend vs Weekday**: Lower weekend demand
- **Seasonal Trends**: Higher summer demand (AC usage)

### **Weather Impact**
- **Temperature Correlation**: Strong correlation with extreme temperatures
- **Humidity Impact**: High humidity increases cooling demand
- **Wind Effect**: Wind can affect renewable generation

### **Trading Signals**
- **High Volatility Days**: Large demand swings = trading opportunities
- **Peak Demand Events**: Extreme weather events
- **Forecast Uncertainty**: Wide confidence intervals = risk/opportunity

### **Optimization Insights**
- **Charging Patterns**: When does the battery charge/discharge?
- **SOC Management**: How is state-of-charge optimized?
- **Profit Maximization**: Which hours generate most profit?

## 🎯 Business Questions to Answer

1. **What are the peak demand hours?** → Grid capacity planning
2. **How does weather affect demand?** → Weather hedging strategies  
3. **Which days have highest volatility?** → Trading opportunity identification
4. **How accurate are our forecasts?** → Model improvement
5. **What's the optimal battery strategy?** → Dispatch optimization
6. **Are there seasonal patterns?** → Long-term planning

## 📈 Visualization Recommendations

- **Time Series**: Demand over time with seasonal decomposition
- **Heatmaps**: Hour-of-day vs day-of-week demand patterns
- **Scatter Plots**: Temperature vs demand correlation
- **Box Plots**: Demand distribution by hour/day/month
- **Trading Charts**: Actual vs forecast with uncertainty bands

## 🔧 Advanced Analytics

- **Rolling Averages**: 24h, 7d, 30d trends
- **Seasonal Decomposition**: Trend, seasonal, residual components
- **Correlation Analysis**: Multi-variable relationships
- **Anomaly Detection**: Statistical outlier identification
- **Forecast Accuracy**: MAPE, RMSE, directional accuracy

---

**💡 Pro Tip**: Start with the basic overview queries, then dive deeper into specific patterns that interest you. The trading chart in `notebooks/01_forecast.ipynb` provides the visual foundation for understanding forecast vs actual patterns.
