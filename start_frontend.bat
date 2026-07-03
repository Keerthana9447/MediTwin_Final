@echo off
REM ═══════════════════════════════════════════════════════════════
REM  MediTwin AI — Windows Frontend Startup
REM  Run AFTER start_backend.bat is running
REM ═══════════════════════════════════════════════════════════════

cd /d "%~dp0frontend"

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║             MediTwin AI — Frontend Startup               ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM ── Check Node ────────────────────────────────────────────────
node --version 2>NUL
if errorlevel 1 (
    echo ERROR: Node.js not found. Install Node.js 20+ from nodejs.org
    pause
    exit /b 1
)

REM ── Create .env.local if missing ──────────────────────────────
if not exist ".env.local" (
    echo VITE_API_URL=http://localhost:8000 > .env.local
    echo Created .env.local
)

REM ── Install npm packages ──────────────────────────────────────
if not exist "node_modules" (
    echo Installing npm packages...
    npm install
)

echo.
echo ═══════════════════════════════════════════════════════════
echo   MediTwin AI frontend starting...
echo   URL: http://localhost:5173
echo   Press CTRL+C to stop
echo ═══════════════════════════════════════════════════════════
echo.
npm run dev
pause
