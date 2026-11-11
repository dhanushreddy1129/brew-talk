#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

echo ""
echo "  ____                     _____     _ _    "
echo " | __ ) _ __ _____      __|_   _|_ _| | | __"
echo " |  _ \| '__/ _ \ \ /\ / /  | |/ _\` | | |/ /"
echo " | |_) | | |  __/\ V  V /   | | (_| | |   < "
echo " |____/|_|  \___| \_/\_/    |_|\__,_|_|_|\_\\"
echo ""
echo " Voice-Order QR Menu for Cafes"
echo " =============================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.12+"
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
echo "[2/3] Installing dependencies..."
source venv/bin/activate
pip install -r backend/requirements.txt --quiet

# Create data directory
mkdir -p data

# Copy .env if needed
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    cp backend/.env.example backend/.env
    echo "[INFO] Created backend/.env from .env.example"
fi

# Start server
echo "[3/3] Starting Brew Talk on http://localhost:8000"
echo ""
echo "  Customer menu:  http://localhost:8000/m/1"
echo "  Kitchen board:  http://localhost:8000/kitchen"
echo "  Admin panel:    http://localhost:8000/admin"
echo "  API docs:       http://localhost:8000/docs"
echo "  Health check:   http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
