#!/bin/bash
# MediTwin AI — Frontend Startup Script

set -e
cd "$(dirname "$0")/frontend"

if [ ! -f ".env.local" ]; then
  echo "VITE_API_URL=http://localhost:8000" > .env.local
fi

if [ ! -d "node_modules" ]; then
  echo "📦 Installing npm packages..."
  npm install
fi

echo "🚀 Starting MediTwin AI frontend on http://localhost:5173"
npm run dev
