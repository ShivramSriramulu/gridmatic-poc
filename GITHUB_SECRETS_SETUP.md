# GitHub Actions Secrets Setup Guide

## Required Secrets

Add these secrets in GitHub → Settings → Secrets and variables → Actions:

### Required for all setups:
- `GCP_PROJECT` = `gridmatic-473617`
- `EIA_API_KEY` = `jSszdnPAMf6uVthB8xx31deYd6jTRaoJapk0Mg8u`

### Authentication Options (choose one):

#### Option A: Workload Identity Federation (Recommended)
- `GCP_WORKLOAD_IDP` = Workload Identity Provider resource name
- `GCP_SA_EMAIL` = Service account email (e.g., `github-actions@gridmatic-473617.iam.gserviceaccount.com`)

#### Option B: Service Account JSON Key
- `GCP_SA_KEY_JSON` = Complete JSON key file content (paste the entire JSON)

## Setup Instructions

1. **For WIF (Option A):**
   - Create a Workload Identity Pool in GCP
   - Create a Service Account with BigQuery permissions
   - Configure the GitHub Actions workflow to use WIF

2. **For SA JSON (Option B):**
   - Create a Service Account in GCP
   - Download the JSON key
   - Paste the entire JSON content as `GCP_SA_KEY_JSON` secret
   - Set `GCP_AUTH_METHOD: KEY` in the workflow

## Testing

You can manually trigger the workflow:
1. Go to Actions tab in GitHub
2. Select "Nightly Pipeline"
3. Click "Run workflow"

The workflow will run at 10:05 UTC daily automatically.
