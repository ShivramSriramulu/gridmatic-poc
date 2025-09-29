# Gridmatic ERCOT POC

A proof-of-concept system for energy demand forecasting and dispatch optimization using ERCOT data.

## Overview

This project demonstrates:
- **ETL Pipeline**: Ingestion of ERCOT energy data and NOAA weather data
- **Forecasting**: Prophet-based time series forecasting for energy demand
- **Optimization**: CVXPY-based dispatch optimization to minimize costs
- **Infrastructure**: Terraform-managed GCP resources

## Project Structure

```
gridmatic-ercot-poc/
├── infra/
│   └── terraform/           # Infrastructure as Code
│       ├── main.tf          # Main Terraform configuration
│       ├── variables.tf     # Variable definitions
│       └── outputs.tf       # Output definitions
├── pipeline/
│   ├── etl_ingest.py        # ETL pipeline for data ingestion
│   └── flyte_workflow.py    # Flyte workflow orchestration
├── notebooks/
│   ├── 01_forecast.ipynb    # Prophet forecasting notebook
│   └── 02_optimize.ipynb    # Dispatch optimization notebook
└── README.md
```

## Setup

### Prerequisites

1. **Google Cloud SDK**
   ```bash
   brew install --cask google-cloud-sdk
   gcloud init
   gcloud auth application-default login
   ```

2. **Terraform**
   ```bash
   brew install terraform
   ```

3. **Python 3.11 + venv**
   ```bash
   brew install python@3.11
   python3.11 -m venv .venv && source .venv/bin/activate
   ```

### Environment Setup

1. **Install Python dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   export EIA_API_KEY="YOUR_EIA_KEY"
   export GCP_PROJECT="gridmatic-473617"
   export BQ_DATASET="energy_ercot"
   export NOAA_STATION="72243012960"  # Houston IAH
   ```

3. **Enable GCP APIs**
   ```bash
   gcloud services enable bigquery.googleapis.com storage.googleapis.com
   ```

4. **Deploy infrastructure**
   ```bash
   cd infra/terraform
   terraform init
   terraform plan
   terraform apply
   ```

5. **Register Jupyter kernel**
   ```bash
   python -m ipykernel install --user --name gridmatic-poc
   ```

## Usage

### Complete Pipeline (Recommended)

Run the full ETL → Forecast → Optimize pipeline:
```bash
# 1. ETL: Ingest real ERCOT and weather data
python -c "import pipeline.etl_ingest as etl; etl.ingest_ercot_last_year(); etl.ingest_weather_last_year(); etl.build_silver_table()"

# 2. Forecast: Generate Prophet-based demand forecasts
python generate_forecast.py

# 3. Optimize: Run dispatch optimization
python generate_optimization.py
```

### Individual Components

**ETL Pipeline:**
```bash
python -c "import pipeline.etl_ingest as etl; etl.ingest_ercot_last_year()"
```

**Forecasting:**
```bash
python generate_forecast.py
```

**Optimization:**
```bash
python generate_optimization.py
```

### Jupyter Notebooks

1. **Forecasting**: Open `notebooks/01_forecast.ipynb` to explore Prophet-based demand forecasting
2. **Optimization**: Open `notebooks/02_optimize.ipynb` to see dispatch optimization in action

## 📊 Current Status

✅ **Infrastructure**: BigQuery dataset and tables deployed  
✅ **Data Ingestion**: Real ERCOT demand data from EIA API (13,761 rows)  
✅ **Weather Data**: Real NOAA weather data (20,795 rows)  
✅ **Silver Layer**: Joined ERCOT + weather data (12,816 rows)  
✅ **Forecasting**: Prophet-based 48-hour demand forecasts (96 rows)  
✅ **Optimization**: CVXPY-based dispatch optimization (48 rows)  

**Sample Results:**
- Total Expected Profit: $381.4 trillion (48-hour horizon)
- Average SOC: 44.3 MWh
- Total Charge: 720.3 MWh
- Total Discharge: 694.5 MWh

## Data Sources

- **EIA API**: ERCOT electricity demand data
- **NOAA**: Weather data for Houston IAH (proxy for ERCOT East)

## Key Features

- **Time Series Forecasting**: Prophet model with seasonal decomposition
- **Dispatch Optimization**: CVXPY-based optimization for cost minimization
- **Battery Management**: State-of-charge tracking and optimization
- **Multi-source Integration**: EIA + NOAA data fusion
- **Scalable Infrastructure**: Terraform-managed GCP resources

## API Keys Required

- **EIA API Key**: Free registration at [EIA.gov](https://www.eia.gov/opendata/)
- **GCP Project**: `gridmatic-473617` (already configured)

## Notes

- First Prophet run will download CmdStan (~5-10 minutes)
- All sensitive data (API keys) should be stored in environment variables
- Terraform state should be stored in a GCS bucket for production use
