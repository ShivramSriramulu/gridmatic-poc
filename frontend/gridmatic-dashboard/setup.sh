#!/bin/bash
# Gridmatic Dashboard Setup Script

echo "🚀 Setting up Gridmatic ERCOT POC Dashboard..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the dashboard root directory"
    echo "   cd frontend/gridmatic-dashboard && ./setup.sh"
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

echo "🔧 Setting up environment..."
if [ ! -f ".env.local" ]; then
    cp env.example .env.local
    echo "✅ Created .env.local from template"
    echo "⚠️  Please edit .env.local with your GCP credentials"
else
    echo "✅ .env.local already exists"
fi

echo "🔑 Setting up Google Cloud credentials..."
echo "📋 Next steps:"
echo "   1. Go to GCP Console → IAM → Service Accounts"
echo "   2. Create new service account"
echo "   3. Grant 'BigQuery Data Viewer' role"
echo "   4. Download JSON key as 'gridmatic-bq-key.json'"
echo "   5. Place the key file in this directory"
echo "   6. Update .env.local with correct paths"

echo ""
echo "🚀 To start the dashboard:"
echo "   npm run dev"
echo ""
echo "🌐 Dashboard will be available at: http://localhost:3000"
echo ""
echo "📊 Make sure your BigQuery tables are populated:"
echo "   - gold_forecasts (Prophet forecasts)"
echo "   - gold_optimizer_outputs (Battery optimization)"
echo ""
echo "✅ Setup complete!"
