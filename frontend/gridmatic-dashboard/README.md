# Gridmatic ERCOT POC Dashboard

A Next.js dashboard for visualizing real-time energy forecasting and battery optimization data from the Gridmatic ERCOT Proof of Concept.

## 🚀 Features

- **Real-time Data**: Live connection to Google BigQuery
- **Trading Forecast**: Prophet-based demand forecasting with uncertainty bands
- **Battery Optimization**: CVXPY-based dispatch optimization visualization
- **Auto-refresh**: Updates every 5 minutes
- **Responsive Design**: Works on desktop and mobile
- **Professional UI**: Clean, modern interface with Tailwind CSS

## 📊 Data Sources

- **ERCOT Demand**: Real hourly demand data from EIA API
- **Weather Data**: NOAA weather data for correlation analysis
- **Forecasts**: Prophet-generated 48-hour demand predictions
- **Optimization**: Battery charge/discharge optimization results

## 🛠️ Setup

### Prerequisites

1. **Google Cloud Project**: `gridmatic-473617`
2. **BigQuery Dataset**: `energy_ercot` with populated tables
3. **Service Account**: With BigQuery Data Viewer permissions

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env.local
   ```

3. **Configure `.env.local`**:
   ```env
   GCP_PROJECT=gridmatic-473617
   BQ_DATASET=energy_ercot
   GOOGLE_APPLICATION_CREDENTIALS=./gridmatic-bq-key.json
   ```

4. **Create Service Account**:
   - Go to GCP Console → IAM → Service Accounts
   - Create new service account
   - Grant "BigQuery Data Viewer" role
   - Download JSON key as `gridmatic-bq-key.json`
   - Place in project root

5. **Run development server**:
   ```bash
   npm run dev
   ```

6. **Open dashboard**: http://localhost:3000

## 🏗️ Architecture

### API Routes

- **`/api/forecast`**: Fetches Prophet forecast data from `gold_forecasts`
- **`/api/optimizer`**: Fetches battery optimization data from `gold_optimizer_outputs`

### Components

- **`TradingChart`**: Line chart showing forecast vs actual with uncertainty bands
- **`BatteryChart`**: Combined bar/line chart showing charge/discharge and SOC

### Data Flow

```
BigQuery Tables → Next.js API Routes → React Components → Charts
```

## 📈 Charts

### Trading Forecast Chart
- **Blue line**: Prophet forecast (yhat)
- **Shaded area**: Confidence interval (yhat_lower to yhat_upper)
- **X-axis**: Time (48-hour horizon)
- **Y-axis**: Demand (MW)

### Battery Optimization Chart
- **Green bars**: Charge operations (positive)
- **Red bars**: Discharge operations (negative)
- **Purple line**: State of Charge (SOC) tracking
- **Metrics**: Total charge/discharge, average SOC, expected profit

## 🔄 Real-time Updates

- **Auto-refresh**: Every 5 minutes
- **Manual refresh**: Reload page
- **Error handling**: Graceful fallbacks for API failures
- **Loading states**: Spinner indicators during data fetch

## 🚀 Deployment

### Vercel (Recommended)

1. **Connect repository** to Vercel
2. **Add environment variables**:
   - `GCP_PROJECT`: `gridmatic-473617`
   - `BQ_DATASET`: `energy_ercot`
   - `GOOGLE_APPLICATION_CREDENTIALS`: Paste JSON key content
3. **Deploy**: Automatic deployment on push

### Other Platforms

- **Netlify**: Similar to Vercel
- **Railway**: Supports environment variables
- **AWS Amplify**: Full-stack deployment

## 🔧 Customization

### Chart Styling
- Modify colors in component files
- Adjust chart options in `options` objects
- Change refresh intervals in `useEffect`

### Data Queries
- Update SQL queries in API routes
- Add new endpoints for additional data
- Modify data processing in components

### UI/UX
- Update Tailwind classes for styling
- Add new components for additional metrics
- Modify layout in `page.tsx`

## 📊 BigQuery Tables

### Required Tables

1. **`gold_forecasts`**:
   - `timestamp_hour`: TIMESTAMP
   - `yhat`: FLOAT (forecast)
   - `yhat_lower`: FLOAT (lower bound)
   - `yhat_upper`: FLOAT (upper bound)

2. **`gold_optimizer_outputs`**:
   - `timestamp_hour`: TIMESTAMP
   - `price`: FLOAT
   - `charge_mwh`: FLOAT
   - `discharge_mwh`: FLOAT
   - `soc_mwh`: FLOAT
   - `bid_mwh`: FLOAT
   - `expected_profit`: FLOAT

## 🐛 Troubleshooting

### Common Issues

1. **"Failed to fetch data"**:
   - Check service account permissions
   - Verify BigQuery tables exist
   - Check environment variables

2. **Charts not loading**:
   - Check browser console for errors
   - Verify API routes are working
   - Check data format matches expected types

3. **Authentication errors**:
   - Verify `GOOGLE_APPLICATION_CREDENTIALS` path
   - Check service account JSON key validity
   - Ensure BigQuery API is enabled

### Debug Mode

Add console logging to API routes:
```typescript
console.log("Query result:", rows);
```

## 📝 License

This project is part of the Gridmatic ERCOT Proof of Concept.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

## 📞 Support

For issues or questions:
- Check the main POC README
- Review BigQuery table schemas
- Verify data pipeline is running