# 🚀 Gridmatic ERCOT POC - Automation Setup Guide

This guide covers setting up the complete automation pipeline including nightly runs and CI/CD.

## 📋 Prerequisites

1. **GitHub Repository**: Code pushed to GitHub
2. **Google Cloud Service Account**: With BigQuery permissions
3. **Vercel Account**: For frontend deployment
4. **GitHub Secrets**: Configured with credentials

## 🔧 Step 1: GitHub Secrets Configuration

### Required Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

#### **GCP_SA_KEY**
```json
{
  "type": "service_account",
  "project_id": "gridmatic-473617",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "gridmatic-sa@gridmatic-473617.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/gridmatic-sa%40gridmatic-473617.iam.gserviceaccount.com"
}
```

#### **EIA_API_KEY**
```
jSszdnPAMf6uVthB8xx31deYd6jTRaoJapk0Mg8u
```

#### **VERCEL_TOKEN**
```
vercel_token_from_vercel_dashboard
```

#### **VERCEL_ORG_ID**
```
vercel_org_id_from_vercel_dashboard
```

#### **VERCEL_PROJECT_ID**
```
vercel_project_id_from_vercel_dashboard
```

### Service Account Setup

1. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create gridmatic-sa \
     --display-name="Gridmatic Automation" \
     --description="Service account for Gridmatic ERCOT POC automation"
   ```

2. **Grant Permissions**:
   ```bash
   gcloud projects add-iam-policy-binding gridmatic-473617 \
     --member="serviceAccount:gridmatic-sa@gridmatic-473617.iam.gserviceaccount.com" \
     --role="roles/bigquery.dataEditor"
   
   gcloud projects add-iam-policy-binding gridmatic-473617 \
     --member="serviceAccount:gridmatic-sa@gridmatic-473617.iam.gserviceaccount.com" \
     --role="roles/bigquery.jobUser"
   ```

3. **Download Key**:
   ```bash
   gcloud iam service-accounts keys create gridmatic-sa-key.json \
     --iam-account=gridmatic-sa@gridmatic-473617.iam.gserviceaccount.com
   ```

## 🔄 Step 2: Nightly Automation

### Workflow Overview

The nightly automation runs at **10:05 PM UTC** (5:05 PM EST, 2:05 PM PST) and:

1. **ETL Refresh**: Pulls fresh ERCOT and weather data
2. **Forecast Generation**: Creates 48-hour Prophet forecasts
3. **Battery Optimization**: Runs CVXPY optimization
4. **Data Quality Check**: Verifies results

### Manual Trigger

You can manually trigger the nightly workflow:

1. Go to GitHub → Actions → "Nightly Automation"
2. Click "Run workflow"
3. Select branch and click "Run workflow"

### Monitoring

- **Success**: Dashboard shows fresh data
- **Failure**: Check GitHub Actions logs
- **Notifications**: Configure Slack/email notifications if needed

## 🏗️ Step 3: CI/CD Pipeline

### Pipeline Stages

1. **Python Tests**: Linting, formatting, type checking, unit tests
2. **Frontend Tests**: ESLint, TypeScript, build verification
3. **Integration Tests**: End-to-end pipeline testing
4. **Security Scan**: Vulnerability scanning with Trivy
5. **Deploy**: Automatic Vercel deployment on main branch
6. **Performance**: Lighthouse CI performance testing

### Trigger Conditions

- **Push to main/develop**: Full pipeline
- **Pull Request**: Tests and security scan only
- **Main branch**: Includes deployment

### Quality Gates

- ✅ All tests must pass
- ✅ No linting errors
- ✅ TypeScript compilation successful
- ✅ Security scan clean
- ✅ Performance scores meet thresholds

## 🚀 Step 4: Vercel Deployment

### Automatic Deployment

The CI/CD pipeline automatically deploys to Vercel when:

- Code is pushed to `main` branch
- All tests pass
- Build is successful

### Environment Variables

Configure these in Vercel dashboard:

```
GCP_PROJECT=gridmatic-473617
BQ_DATASET=energy_ercot
GOOGLE_APPLICATION_CREDENTIALS=<service_account_json>
```

### Custom Domain (Optional)

1. Go to Vercel dashboard → Project → Settings → Domains
2. Add custom domain: `dashboard.gridmatic.com`
3. Configure DNS records

## 📊 Step 5: Monitoring & Alerting

### GitHub Actions Monitoring

- **Workflow Status**: Check Actions tab regularly
- **Run History**: View past runs and logs
- **Failure Notifications**: GitHub will email on failures

### Dashboard Monitoring

- **Data Freshness**: Check timestamp of latest data
- **Error States**: Dashboard shows loading/error states
- **Performance**: Monitor page load times

### Custom Alerts (Optional)

Add Slack/email notifications:

```yaml
- name: Notify on Failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🔧 Troubleshooting

### Common Issues

#### **Authentication Errors**
```bash
# Check service account permissions
gcloud projects get-iam-policy gridmatic-473617

# Verify BigQuery access
gcloud auth list
```

#### **Build Failures**
```bash
# Test locally
cd frontend/gridmatic-dashboard
npm run build

# Check TypeScript errors
npx tsc --noEmit
```

#### **Data Pipeline Errors**
```bash
# Test ETL locally
python -c "import pipeline.etl_ingest as etl; etl.ingest_ercot_last_year()"

# Check BigQuery tables
bq ls energy_ercot
```

### Debug Commands

#### **Test Nightly Workflow Locally**
```bash
# Set environment variables
export GCP_PROJECT=gridmatic-473617
export BQ_DATASET=energy_ercot
export EIA_API_KEY=your_key

# Run ETL
python -c "import pipeline.etl_ingest as etl; etl.ingest_ercot_last_year(); etl.ingest_weather_last_year(); etl.build_silver_table()"

# Run forecast
python generate_forecast.py

# Run optimization
python generate_optimization.py
```

#### **Test Frontend Locally**
```bash
cd frontend/gridmatic-dashboard
npm install
npm run dev
```

## 📈 Performance Optimization

### GitHub Actions Optimization

- **Caching**: Pip and npm dependencies cached
- **Parallel Jobs**: Tests run in parallel
- **Conditional Deployment**: Only deploy on main branch

### Dashboard Optimization

- **Auto-refresh**: Every 5 minutes
- **Error Handling**: Graceful fallbacks
- **Loading States**: User feedback during data fetch

## 🔒 Security Best Practices

### Secrets Management

- ✅ Never commit secrets to code
- ✅ Use GitHub Secrets for sensitive data
- ✅ Rotate service account keys regularly
- ✅ Limit service account permissions

### Code Security

- ✅ Dependency scanning with Trivy
- ✅ Regular security updates
- ✅ Input validation in API routes
- ✅ CORS configuration for frontend

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel Deployment Guide](https://vercel.com/docs)
- [Google Cloud IAM](https://cloud.google.com/iam/docs)
- [BigQuery Best Practices](https://cloud.google.com/bigquery/docs/best-practices)

## 🎯 Success Metrics

### Automation Success

- ✅ Nightly runs complete successfully
- ✅ Dashboard shows fresh data daily
- ✅ CI/CD pipeline passes consistently
- ✅ Zero-downtime deployments

### Performance Metrics

- ✅ Page load time < 3 seconds
- ✅ Lighthouse score > 90
- ✅ API response time < 1 second
- ✅ 99.9% uptime

---

**🎉 Congratulations!** Your Gridmatic ERCOT POC now has production-ready automation with nightly data refresh and continuous deployment!
