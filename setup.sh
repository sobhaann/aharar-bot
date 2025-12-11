#!/bin/bash
# Setup script for local development

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env

echo "✅ Setup complete! Please edit .env with your credentials and run: python main.py"
