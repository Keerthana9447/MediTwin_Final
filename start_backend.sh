#!/bin/bash
# MediTwin AI — Backend Startup Script
# Usage: ./start_backend.sh

set -e
cd "$(dirname "$0")/backend"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "⚠️  Created .env from template — add your GROQ_API_KEY"
fi

if [ ! -d ".venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
echo "📚 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "🚀 Starting MediTwin AI backend on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level info
