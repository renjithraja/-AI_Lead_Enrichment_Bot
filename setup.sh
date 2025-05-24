#!/bin/bash

# AI Lead Enrichment Bot - Setup Script
echo "🤖 AI Lead Enrichment Bot Setup"
echo "================================"

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ Found: $python_version"
else
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing requirements..."
pip install -r requirements.txt

# Create sample files
echo "📄 Creating sample input file..."
cat > sample_companies.csv << EOF
company_name
OpenAI
DeepMind
Zoho
Freshworks
Stripe
Slack
Notion
Figma
Canva
Spotify
EOF

echo "✅ Sample file created: sample_companies.csv"

# Create .env template
echo "🔐 Creating environment template..."
cat > .env.template << EOF
# Get your free Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: OpenAI API key (if you want to use GPT instead)
# OPENAI_API_KEY=your_openai_api_key_here
EOF

echo "📝 Environment template created: .env.template"

# Check if .env exists
if [[ ! -f ".env" ]]; then
    cp .env.template .env
    echo "📋 Environment file created: .env"
    echo "⚠️  Please edit .env and add your Gemini API key"
else
    echo "ℹ️  .env file already exists"
fi

# Make scripts executable
chmod +x run.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Get your free Gemini API key: https://makersuite.google.com/app/apikey"
echo "2. Edit .env file and add your API key"
echo "3. Run the bot:"
echo "   - Web interface: python run.py --mode web"
echo "   - Command line: python run.py --mode cli"
echo ""
echo "💡 Quick start: python run.py"
echo ""