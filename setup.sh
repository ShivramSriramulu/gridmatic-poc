#!/bin/bash
# Setup script for Gridmatic ERCOT POC

set -e

echo "🚀 Setting up Gridmatic ERCOT POC environment..."

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Please run this script from the gridmatic-ercot-poc directory"
    exit 1
fi

# Install system dependencies
echo "📦 Installing system dependencies..."
if command -v brew &> /dev/null; then
    echo "Installing Google Cloud SDK..."
    brew install --cask google-cloud-sdk
    
    echo "Installing Terraform..."
    brew install terraform
    
    echo "Installing Python 3.11..."
    brew install python@3.11
else
    echo "❌ Homebrew not found. Please install dependencies manually:"
    echo "   - Google Cloud SDK"
    echo "   - Terraform"
    echo "   - Python 3.11"
fi

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3.11 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install requirements
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Register Jupyter kernel
echo "📓 Registering Jupyter kernel..."
python -m ipykernel install --user --name gridmatic-poc

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Set up environment variables:"
echo "   cp env.example .env.local"
echo "   # Edit .env.local with your API keys"
echo ""
echo "2. Authenticate with Google Cloud:"
echo "   gcloud init"
echo "   gcloud auth application-default login"
echo ""
echo "3. Enable GCP APIs:"
echo "   gcloud services enable bigquery.googleapis.com storage.googleapis.com"
echo ""
echo "4. Deploy infrastructure:"
echo "   cd infra/terraform"
echo "   terraform init"
echo "   terraform apply"
echo ""
echo "5. Activate virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "6. Run notebooks:"
echo "   jupyter lab notebooks/"
echo ""
echo "🎉 Happy coding!"
