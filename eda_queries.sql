-- =====================================================
-- GRIDMATIC ERCOT POC - EXPLORATORY DATA ANALYSIS
-- =====================================================
-- Run these queries in BigQuery to explore your energy data
-- Replace 'gridmatic-473617' with your actual project ID

-- =====================================================
-- 1. DATA OVERVIEW & QUALITY CHECKS
-- =====================================================

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
FROM `gridmatic-473617.energy_ercot.silver_ercot_weather`
UNION ALL
SELECT 
  'gold_forecasts' as table_name,
  COUNT(*) as row_count,
  MIN(timestamp_hour) as earliest_data,
  MAX(timestamp_hour) as latest_data,
  COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
FROM `gridmatic-473617.energy_ercot.gold_forecasts`
UNION ALL
SELECT 
  'gold_optimizer_outputs' as table_name,
  COUNT(*) as row_count,
  MIN(timestamp_hour) as earliest_data,
  MAX(timestamp_hour) as latest_data,
  COUNT(DISTINCT DATE(timestamp_hour)) as unique_days
FROM `gridmatic-473617.energy_ercot.gold_optimizer_outputs`;

-- =====================================================
-- 2. ERCOT DEMAND ANALYSIS
-- =====================================================

-- Daily demand patterns
SELECT 
  DATE(timestamp_hour) as date,
  AVG(demand_mw) as avg_demand_mw,
  MIN(demand_mw) as min_demand_mw,
  MAX(demand_mw) as max_demand_mw,
  STDDEV(demand_mw) as demand_stddev,
  COUNT(*) as hourly_readings
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
ORDER BY date DESC
LIMIT 30;

-- Hourly demand patterns (time of day analysis)
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

-- Weekly demand patterns
SELECT 
  EXTRACT(DAYOFWEEK FROM timestamp_hour) as day_of_week,
  CASE EXTRACT(DAYOFWEEK FROM timestamp_hour)
    WHEN 1 THEN 'Sunday'
    WHEN 2 THEN 'Monday'
    WHEN 3 THEN 'Tuesday'
    WHEN 4 THEN 'Wednesday'
    WHEN 5 THEN 'Thursday'
    WHEN 6 THEN 'Friday'
    WHEN 7 THEN 'Saturday'
  END as day_name,
  AVG(demand_mw) as avg_demand_mw,
  MIN(demand_mw) as min_demand_mw,
  MAX(demand_mw) as max_demand_mw
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY EXTRACT(DAYOFWEEK FROM timestamp_hour), day_name
ORDER BY day_of_week;

-- Monthly demand trends
SELECT 
  EXTRACT(MONTH FROM timestamp_hour) as month,
  EXTRACT(YEAR FROM timestamp_hour) as year,
  AVG(demand_mw) as avg_demand_mw,
  MIN(demand_mw) as min_demand_mw,
  MAX(demand_mw) as max_demand_mw,
  COUNT(*) as hourly_readings
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY EXTRACT(MONTH FROM timestamp_hour), EXTRACT(YEAR FROM timestamp_hour)
ORDER BY year, month;

-- =====================================================
-- 3. WEATHER CORRELATION ANALYSIS
-- =====================================================

-- Temperature vs Demand correlation
SELECT 
  DATE(timestamp_hour) as date,
  AVG(temp_celsius) as avg_temp_c,
  AVG(demand_mw) as avg_demand_mw,
  CORR(temp_celsius, demand_mw) as temp_demand_correlation
FROM `gridmatic-473617.energy_ercot.silver_ercot_weather`
WHERE temp_celsius IS NOT NULL AND demand_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
HAVING COUNT(*) >= 20  -- Only days with sufficient data
ORDER BY date DESC
LIMIT 30;

-- Weather extremes and demand impact
SELECT 
  CASE 
    WHEN temp_celsius < 10 THEN 'Cold (<10°C)'
    WHEN temp_celsius BETWEEN 10 AND 25 THEN 'Moderate (10-25°C)'
    WHEN temp_celsius > 25 THEN 'Hot (>25°C)'
  END as temp_category,
  COUNT(*) as hours,
  AVG(demand_mw) as avg_demand_mw,
  AVG(wind_speed_mps) as avg_wind_speed,
  AVG(humidity_pct) as avg_humidity
FROM `gridmatic-473617.energy_ercot.silver_ercot_weather`
WHERE temp_celsius IS NOT NULL AND demand_mw IS NOT NULL
GROUP BY temp_category
ORDER BY avg_demand_mw DESC;

-- =====================================================
-- 4. FORECASTING ANALYSIS
-- =====================================================

-- Forecast accuracy analysis (if you have actual vs predicted)
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

-- Forecast horizon analysis
SELECT 
  EXTRACT(HOUR FROM timestamp_hour) as forecast_hour,
  AVG(yhat) as avg_forecast_mw,
  STDDEV(yhat) as forecast_stddev,
  AVG(yhat_upper - yhat_lower) as avg_uncertainty
FROM `gridmatic-473617.energy_ercot.gold_forecasts`
GROUP BY EXTRACT(HOUR FROM timestamp_hour)
ORDER BY forecast_hour;

-- =====================================================
-- 5. OPTIMIZATION ANALYSIS
-- =====================================================

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

-- Charging patterns by hour
SELECT 
  EXTRACT(HOUR FROM timestamp_hour) as hour_of_day,
  AVG(charge_mwh) as avg_charge_mwh,
  AVG(discharge_mwh) as avg_discharge_mwh,
  AVG(soc_mwh) as avg_soc_mwh,
  COUNT(*) as observations
FROM `gridmatic-473617.energy_ercot.gold_optimizer_outputs`
GROUP BY EXTRACT(HOUR FROM timestamp_hour)
ORDER BY hour_of_day;

-- Profit analysis
SELECT 
  SUM(expected_profit) as total_profit,
  AVG(expected_profit) as avg_hourly_profit,
  MAX(expected_profit) as max_hourly_profit,
  MIN(expected_profit) as min_hourly_profit,
  STDDEV(expected_profit) as profit_stddev
FROM `gridmatic-473617.energy_ercot.gold_optimizer_outputs`;

-- =====================================================
-- 6. DATA QUALITY & ANOMALY DETECTION
-- =====================================================

-- Missing data analysis
SELECT 
  'bronze_ercot' as table_name,
  COUNT(*) as total_rows,
  COUNT(demand_mw) as non_null_demand,
  COUNT(*) - COUNT(demand_mw) as missing_demand,
  ROUND((COUNT(*) - COUNT(demand_mw)) / COUNT(*) * 100, 2) as missing_pct
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
UNION ALL
SELECT 
  'bronze_weather' as table_name,
  COUNT(*) as total_rows,
  COUNT(temp_celsius) as non_null_temp,
  COUNT(*) - COUNT(temp_celsius) as missing_temp,
  ROUND((COUNT(*) - COUNT(temp_celsius)) / COUNT(*) * 100, 2) as missing_pct
FROM `gridmatic-473617.energy_ercot.bronze_weather`;

-- Outlier detection (demand values outside 3 standard deviations)
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

-- =====================================================
-- 7. TIME SERIES ANALYSIS
-- =====================================================

-- Demand growth trends (monthly)
SELECT 
  EXTRACT(YEAR FROM timestamp_hour) as year,
  EXTRACT(MONTH FROM timestamp_hour) as month,
  AVG(demand_mw) as avg_demand_mw,
  LAG(AVG(demand_mw)) OVER (ORDER BY EXTRACT(YEAR FROM timestamp_hour), EXTRACT(MONTH FROM timestamp_hour)) as prev_month_avg,
  AVG(demand_mw) - LAG(AVG(demand_mw)) OVER (ORDER BY EXTRACT(YEAR FROM timestamp_hour), EXTRACT(MONTH FROM timestamp_hour)) as month_over_month_change
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY EXTRACT(YEAR FROM timestamp_hour), EXTRACT(MONTH FROM timestamp_hour)
ORDER BY year, month;

-- Peak demand analysis
SELECT 
  DATE(timestamp_hour) as date,
  MAX(demand_mw) as peak_demand_mw,
  EXTRACT(HOUR FROM timestamp_hour) as peak_hour
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
ORDER BY peak_demand_mw DESC
LIMIT 20;

-- =====================================================
-- 8. ADVANCED ANALYTICS
-- =====================================================

-- Rolling averages and trends
SELECT 
  timestamp_hour,
  demand_mw,
  AVG(demand_mw) OVER (
    ORDER BY timestamp_hour 
    ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
  ) as rolling_24h_avg,
  AVG(demand_mw) OVER (
    ORDER BY timestamp_hour 
    ROWS BETWEEN 167 PRECEDING AND CURRENT ROW
  ) as rolling_7d_avg
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
ORDER BY timestamp_hour DESC
LIMIT 100;

-- Seasonal decomposition (simplified)
SELECT 
  EXTRACT(MONTH FROM timestamp_hour) as month,
  AVG(demand_mw) as seasonal_avg,
  MIN(demand_mw) as seasonal_min,
  MAX(demand_mw) as seasonal_max,
  COUNT(*) as sample_size
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL
GROUP BY EXTRACT(MONTH FROM timestamp_hour)
ORDER BY month;

-- =====================================================
-- 9. BUSINESS INTELLIGENCE QUERIES
-- =====================================================

-- Energy trading opportunities (high volatility periods)
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
HAVING COUNT(*) >= 20  -- Complete days only
ORDER BY daily_range DESC
LIMIT 20;

-- System efficiency metrics
SELECT 
  DATE(timestamp_hour) as date,
  AVG(demand_mw) as avg_demand,
  AVG(generation_mw) as avg_generation,
  AVG(generation_mw) / AVG(demand_mw) as efficiency_ratio,
  COUNT(*) as hourly_readings
FROM `gridmatic-473617.energy_ercot.bronze_ercot`
WHERE demand_mw IS NOT NULL AND generation_mw IS NOT NULL
GROUP BY DATE(timestamp_hour)
ORDER BY date DESC
LIMIT 30;
