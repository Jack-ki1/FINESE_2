#!/bin/bash
# Deployment script for Hugging Face Spaces

echo "🚀 FINESE 2 - Deployment Script for Hugging Face Spaces"

# Check if running in Hugging Face environment
if [ ! -z "$SPACE_ID" ]; then
    echo "✅ Detected Hugging Face Space environment"
    echo "Space ID: $SPACE_ID"
fi

# Set appropriate concurrency based on environment
if [ ! -z "$SPACE_ID" ]; then
    export N_JOBS=1
    echo "🔧 Set N_JOBS=1 for Hugging Face Space environment"
else
    export N_JOBS=-1
    echo "🔧 Set N_JOBS=-1 for local environment"
fi

# Create necessary directories
mkdir -p static/uploads static/exports static/reports models flask_session

# Install any additional dependencies that might be needed in the HF environment
pip install --upgrade pip

# Start the application
echo "🌟 Starting FINESE 2 application..."
python app.py