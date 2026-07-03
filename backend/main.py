"""
MediTwin AI — FastAPI Backend
Run from the backend/ directory:
  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
import os, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("meditwin")

from routers import auth, health, ai, reports, triage, family, timemachine, preventive, ml, rag, consensus, reasoning
import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    logger.info("🗄️  SQLite database ready (backend/meditwin.db)")
    logger.info("🧬 MediTwin AI starting — clinical risk engine ready (FINDRISC/Framingham/WHO)")

    groq_key = os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    if not groq_key:
        logger.warning("⚠️  GROQ_API_KEY not set in .env — AI features (Clinical Reasoning Agent, AI Chat, etc.) will fail")
        logger.warning("   Add GROQ_API_KEY=gsk_... and GROQ_MODEL=openai/gpt-oss-120b to backend/.env and restart")
    else:
        logger.info("✅ Groq API key loaded | model: %s", groq_model)

    logger.info("🤖 Clinical Reasoning Agent ready")
    logger.info("✅ Ready on http://localhost:8000  |  Docs: http://localhost:8000/docs")
    yield
    logger.info("🔻 MediTwin AI shutting down")


app = FastAPI(
    title="MediTwin AI",
    description="Digital Health Twin — AI Clinical Reasoning Platform",
    version="2.0.0",
    lifespan=lifespan,
)

ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.requests import Request
from fastapi.responses import JSONResponse

@app.exception_handler(RuntimeError)
async def ai_service_error_handler(request: Request, exc: RuntimeError):
    logger.error(f"AI service error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=502, content={"detail": str(exc)})

# ── Core endpoints ─────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["Auth"])
app.include_router(health.router,     prefix="/api/v1/health",     tags=["Health"])
app.include_router(ai.router,         prefix="/api/v1/ai",         tags=["AI Engine"])
app.include_router(reports.router,    prefix="/api/v1/reports",    tags=["Report Analyzer"])
app.include_router(triage.router,     prefix="/api/v1/triage",     tags=["Emergency Triage"])

# ── Advanced modules ───────────────────────────────────────────
app.include_router(family.router,     prefix="/api/v1/family",     tags=["Family Health Twin"])
app.include_router(timemachine.router,prefix="/api/v1/timemachine",tags=["Health Time Machine"])
app.include_router(preventive.router, prefix="/api/v1/preventive", tags=["Preventive Impact"])
app.include_router(ml.router,         prefix="/api/v1/ml",         tags=["ML Validation Engine"])
app.include_router(rag.router,        prefix="/api/v1/rag",        tags=["RAG Knowledge Base"])

# ── GenAI flagship features ────────────────────────────────────
app.include_router(consensus.router,  prefix="/api/v1/consensus",  tags=["Multi-Agent Consensus"])
app.include_router(reasoning.router,  prefix="/api/v1/reasoning",  tags=["🧠 Clinical Reasoning Agent"])


@app.get("/")
async def root() -> dict:
    return {
        "service": "MediTwin AI",
        "version": "2.0.0",
        "status":  "operational",
        "flagship": "Clinical Reasoning Agent — POST /api/v1/reasoning/analyze",
        "docs":    "http://localhost:8000/docs",
    }

@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
