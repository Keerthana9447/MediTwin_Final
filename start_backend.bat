@echo off
REM ═══════════════════════════════════════════════════════════════
REM  MediTwin AI — Windows Backend Startup
REM  Double-click this file OR run it from Command Prompt
REM ═══════════════════════════════════════════════════════════════

cd /d "%~dp0backend"

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║              MediTwin AI — Backend Startup               ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM ── Check Python version ─────────────────────────────────────
python --version 2>NUL
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

REM ── Create venv if it doesn't exist ──────────────────────────
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Done.
)

REM ── Activate venv ─────────────────────────────────────────────
call .venv\Scripts\activate.bat

REM ── Upgrade pip silently ──────────────────────────────────────
python -m pip install --upgrade pip --quiet

REM ── Install dependencies ──────────────────────────────────────
echo Installing dependencies (using pre-built wheels -- no C compiler needed)...
echo.
pip install -r requirements.txt --prefer-binary --quiet
if errorlevel 1 (
    echo.
    echo INSTALL FAILED. Trying without version pins...
    pip install fastapi uvicorn[standard] pydantic python-jose groq httpx ^
                python-dotenv python-multipart scikit-learn numpy pandas ^
                joblib shap --prefer-binary --quiet
)

REM ── Check .env file ───────────────────────────────────────────
if not exist ".env" (
    copy .env.example .env >NUL
    echo.
    echo ┌─────────────────────────────────────────────────────────┐
    echo │  ACTION REQUIRED: Open backend\.env in Notepad and     │
    echo │  add your GROQ_API_KEY=gsk_your_key_here               │
    echo │  Get a free key at: https://console.groq.com           │
    echo └─────────────────────────────────────────────────────────┘
    echo.
    echo Press any key after editing .env to continue...
    pause >NUL
)

REM ── Train ML models if not already trained ────────────────────
if not exist "ml\models\diabetes\metadata.json" (
    echo.
    echo Training ML models for the first time (takes ~10 seconds)...
    python ml\train_models.py
    echo ML models trained and cached.
)

REM ── Start the API ─────────────────────────────────────────────
echo.
echo ═══════════════════════════════════════════════════════════
echo   MediTwin AI backend starting...
echo   URL:  http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Press CTRL+C to stop
echo ═══════════════════════════════════════════════════════════
echo.
uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause
