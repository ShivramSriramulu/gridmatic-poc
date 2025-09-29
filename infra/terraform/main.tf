terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_bigquery_dataset" "ercot" {
  dataset_id = "energy_ercot"
  location   = "US"
}

# Bronze
resource "google_bigquery_table" "bronze_ercot" {
  dataset_id = google_bigquery_dataset.ercot.dataset_id
  table_id   = "bronze_ercot"
  schema     = jsonencode([
    {name="timestamp_hour", type="TIMESTAMP"},
    {name="demand_mw", type="FLOAT"},
    {name="generation_mw", type="FLOAT"},
    {name="forecast_demand_mw", type="FLOAT"}
  ])
  deletion_protection = false
}

resource "google_bigquery_table" "bronze_weather" {
  dataset_id = google_bigquery_dataset.ercot.dataset_id
  table_id   = "bronze_weather"
  schema     = jsonencode([
    {name="timestamp_hour", type="TIMESTAMP"},
    {name="temp_c", type="FLOAT"},
    {name="wind_speed_mps", type="FLOAT"},
    {name="wind_dir_deg", type="FLOAT"}
  ])
  deletion_protection = false
}

# Silver (clean join) — created once, then overwritten by SQL
resource "google_bigquery_table" "silver_ercot_weather" {
  dataset_id = google_bigquery_dataset.ercot.dataset_id
  table_id   = "silver_ercot_weather"
  schema     = jsonencode([
    {name="timestamp_hour", type="TIMESTAMP"},
    {name="demand_mw", type="FLOAT"},
    {name="generation_mw", type="FLOAT"},
    {name="forecast_demand_mw", type="FLOAT"},
    {name="temp_c", type="FLOAT"},
    {name="wind_speed_mps", type="FLOAT"},
    {name="wind_dir_deg", type="FLOAT"}
  ])
  deletion_protection = false
}

# Gold outputs
resource "google_bigquery_table" "gold_forecasts" {
  dataset_id = google_bigquery_dataset.ercot.dataset_id
  table_id   = "gold_forecasts"
  schema     = jsonencode([
    {name="timestamp_hour", type="TIMESTAMP"},
    {name="yhat", type="FLOAT"},
    {name="yhat_lower", type="FLOAT"},
    {name="yhat_upper", type="FLOAT"},
    {name="created_at", type="TIMESTAMP", mode="NULLABLE"}
  ])
  time_partitioning {
    type  = "DAY"
    field = "timestamp_hour"
  }
  deletion_protection = false
}

resource "google_bigquery_table" "gold_optimizer_outputs" {
  dataset_id = google_bigquery_dataset.ercot.dataset_id
  table_id   = "gold_optimizer_outputs"
  schema     = jsonencode([
    {name="timestamp_hour", type="TIMESTAMP"},
    {name="price", type="FLOAT"},
    {name="charge_mwh", type="FLOAT"},
    {name="discharge_mwh", type="FLOAT"},
    {name="soc_mwh", type="FLOAT"},
    {name="bid_mwh", type="FLOAT"},
    {name="expected_profit", type="FLOAT"}
  ])
  time_partitioning {
    type  = "DAY"
    field = "timestamp_hour"
  }
  deletion_protection = false
}
