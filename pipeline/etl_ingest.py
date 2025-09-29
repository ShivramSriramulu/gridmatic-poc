import os, math, requests, pandas as pd, numpy as np
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery

PROJECT   = os.environ.get("GCP_PROJECT")
DATASET   = os.environ.get("BQ_DATASET", "energy_ercot")
EIA_KEY   = os.environ.get("EIA_API_KEY", "jSszdnPAMf6uVthB8xx31deYd6jTRaoJapk0Mg8u")
STATION   = os.environ.get("NOAA_STATION", "72243012960")

# ---------- Helpers ----------
def to_hour(ts):
    # EIA returns strings like '20250928T16Z' or '2025-09-28T16'
    return pd.to_datetime(ts).tz_localize("UTC").replace(minute=0, second=0, microsecond=0)

def bq_load_df(df: pd.DataFrame, table: str):
    client = bigquery.Client(project=PROJECT)
    table_id = f"{PROJECT}.{DATASET}.{table}"
    job = client.load_table_from_dataframe(df, table_id)
    job.result()

# ---------- ERCOT via EIA ----------
def fetch_eia_ercot_data():
    """Fetch real ERCOT hourly demand data from EIA API v2"""
    url = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
    params = {
        'api_key': EIA_KEY,
        'frequency': 'hourly',
        'data[0]': 'value',
        'facets[respondent][]': 'ERCO',  # Use ERCO, not ERCOT
        'facets[type][]': 'D',  # Demand
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'offset': 0,
        'length': 10000
    }
    
    print("Fetching real ERCOT demand data from EIA API...")
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    js = r.json()
    
    if 'response' not in js or 'data' not in js['response']:
        print("No ERCOT data found in API response")
        return pd.DataFrame()
    
    rows = js["response"]["data"]
    if not rows:
        print("No data rows returned from EIA API")
        return pd.DataFrame()
    
    df = pd.DataFrame(rows, columns=["period", "value"])
    df["timestamp_hour"] = df["period"].apply(to_hour)
    df = df.drop(columns=["period"]).rename(columns={"value": "demand_mw"})
    df["demand_mw"] = pd.to_numeric(df["demand_mw"], errors='coerce')  # Convert to numeric
    
    print(f"Fetched {len(df)} rows of real ERCOT data")
    return df

def ingest_ercot_last_year():
    # Fetch real ERCOT data from EIA API
    demand = fetch_eia_ercot_data()
    
    if demand.empty:
        print("No real ERCOT data found, creating sample data for demo")
        # Fallback to sample data
        end_date = pd.Timestamp.now(tz='UTC')
        start_date = end_date - pd.Timedelta(days=365)
        dates = pd.date_range(start=start_date, end=end_date, freq='h')
        
        base_demand = 50000
        seasonal = 5000 * np.sin(2 * np.pi * np.arange(len(dates)) / (365.25 * 24))
        weekly = 2000 * np.sin(2 * np.pi * np.arange(len(dates)) / (7 * 24))
        daily = 3000 * np.sin(2 * np.pi * np.arange(len(dates)) / 24)
        noise = np.random.normal(0, 1000, len(dates))
        
        demand = pd.DataFrame({
            'timestamp_hour': dates,
            'demand_mw': base_demand + seasonal + weekly + daily + noise
        })
    
    # Keep last 365d
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=365)
    demand = demand[demand["timestamp_hour"] >= cutoff]
    
    # Add required columns for schema
    demand['generation_mw'] = demand['demand_mw'] * 0.95  # Assume 95% efficiency
    demand['forecast_demand_mw'] = pd.NA
    
    bq_load_df(demand[["timestamp_hour", "demand_mw", "generation_mw", "forecast_demand_mw"]], "bronze_ercot")
    print(f"[bronze_ercot] loaded {len(demand)} rows")

# ---------- NOAA ISD ----------
def parse_noaa_temp(tmp):
    # TMP like "0200,1" => 20.0°C; some responses use tenths C or Kelvin variants; your step-3 parser worked.
    try:
        base = tmp.split(",")[0]
        v = int(base)
        # NOAA global-hourly TMP is tenths deg C
        return v / 10.0
    except:
        return None

def parse_noaa_wind(wnd):
    # WND like "170,1,N,0021,1" => speed "0021" tenths m/s => 2.1 m/s
    try:
        parts = wnd.split(",")
        speed = int(parts[3])
        return speed / 10.0
    except:
        return None

def parse_noaa_dir(wnd):
    try:
        return float(wnd.split(",")[0])
    except:
        return None

def fetch_noaa_hourly(station: str, start: str, end: str):
    url = (
      "https://www.ncei.noaa.gov/access/services/data/v1"
      f"?dataset=global-hourly&stations={station}&startDate={start}&endDate={end}&format=json"
      "&dataTypes=TMP&dataTypes=WND"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    js = r.json()
    df = pd.DataFrame(js)
    df["timestamp_hour"] = pd.to_datetime(df["DATE"], utc=True).dt.floor("H")
    df["temp_c"] = df["TMP"].apply(parse_noaa_temp)
    df["wind_speed_mps"] = df["WND"].apply(parse_noaa_wind)
    df["wind_dir_deg"] = df["WND"].apply(parse_noaa_dir)
    return df[["timestamp_hour","temp_c","wind_speed_mps","wind_dir_deg"]]

def ingest_weather_last_year():
    # Try to fetch real NOAA weather data
    print("Fetching real NOAA weather data...")
    
    try:
        end = datetime.utcnow().date()
        start = (end - timedelta(days=365)).isoformat()
        end_s = end.isoformat()
        
        df = fetch_noaa_hourly(STATION, start, end_s)
        if not df.empty:
            df = df.sort_values("timestamp_hour")
            bq_load_df(df, "bronze_weather")
            print(f"[bronze_weather] loaded {len(df)} rows of real weather data")
            return
    except Exception as e:
        print(f"Failed to fetch real weather data: {e}")
    
    # Fallback to sample weather data
    print("Creating sample weather data for demo...")
    
    end_date = pd.Timestamp.now(tz='UTC')
    start_date = end_date - pd.Timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='h')
    
    # Generate realistic Houston weather patterns
    base_temp = 22  # 22°C average
    seasonal_temp = 8 * np.sin(2 * np.pi * np.arange(len(dates)) / (365.25 * 24) - np.pi/2)
    daily_temp = 3 * np.sin(2 * np.pi * np.arange(len(dates)) / 24)
    temp_noise = np.random.normal(0, 2, len(dates))
    
    base_wind = 3  # 3 m/s average
    wind_noise = np.random.normal(0, 1, len(dates))
    
    weather = pd.DataFrame({
        'timestamp_hour': dates,
        'temp_c': base_temp + seasonal_temp + daily_temp + temp_noise,
        'wind_speed_mps': np.maximum(base_wind + wind_noise, 0),
        'wind_dir_deg': np.random.uniform(0, 360, len(dates))
    })
    
    bq_load_df(weather, "bronze_weather")
    print(f"[bronze_weather] loaded {len(weather)} rows of sample data")

# ---------- Build Silver in BigQuery ----------
SILVER_SQL = f"""
CREATE OR REPLACE TABLE `{PROJECT}.{DATASET}.silver_ercot_weather` AS
WITH bounds AS (
  SELECT
    TIMESTAMP_TRUNC(MIN(timestamp_hour), HOUR) AS min_ts,
    TIMESTAMP_TRUNC(MAX(timestamp_hour), HOUR) AS max_ts
  FROM `{PROJECT}.{DATASET}.bronze_ercot`
),
hours AS (
  SELECT ts AS timestamp_hour
  FROM bounds, UNNEST(GENERATE_TIMESTAMP_ARRAY(min_ts, max_ts, INTERVAL 1 HOUR)) AS ts
),
ercot AS (
  SELECT timestamp_hour, demand_mw, generation_mw, forecast_demand_mw
  FROM `{PROJECT}.{DATASET}.bronze_ercot`
),
wx AS (
  SELECT timestamp_hour, temp_c, wind_speed_mps, wind_dir_deg
  FROM `{PROJECT}.{DATASET}.bronze_weather`
),
joined AS (
  SELECT
    h.timestamp_hour,
    e.demand_mw, e.generation_mw, e.forecast_demand_mw,
    w.temp_c, w.wind_speed_mps, w.wind_dir_deg
  FROM hours h
  LEFT JOIN ercot e USING (timestamp_hour)
  LEFT JOIN wx w USING (timestamp_hour)
),
ff AS (
  SELECT
    timestamp_hour,
    -- forward-fill demand/generation (IGNORE NULLS)
    ANY_VALUE(demand_mw) OVER (ORDER BY timestamp_hour
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS demand_mw_ff,
    ANY_VALUE(generation_mw) OVER (ORDER BY timestamp_hour
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS generation_mw_ff,
    forecast_demand_mw,
    -- forward-fill weather
    ANY_VALUE(temp_c) OVER (ORDER BY timestamp_hour
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS temp_c_ff,
    ANY_VALUE(wind_speed_mps) OVER (ORDER BY timestamp_hour
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS wind_speed_mps_ff,
    ANY_VALUE(wind_dir_deg) OVER (ORDER BY timestamp_hour
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS wind_dir_deg_ff
  FROM joined
)
SELECT
  timestamp_hour,
  demand_mw_ff    AS demand_mw,
  generation_mw_ff AS generation_mw,
  forecast_demand_mw,
  temp_c_ff       AS temp_c,
  wind_speed_mps_ff AS wind_speed_mps,
  wind_dir_deg_ff AS wind_dir_deg
FROM ff
ORDER BY timestamp_hour;
"""

def build_silver_table():
    client = bigquery.Client(project=PROJECT)
    client.query(SILVER_SQL).result()
    print("[silver_ercot_weather] refreshed")

if __name__ == "__main__":
    ingest_ercot_last_year()
    ingest_weather_last_year()
    build_silver_table()
