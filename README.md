# 🧬 MediTwin AI — Digital Health Operating System

> **Production-grade AI preventive healthcare platform.**  
> Creates a personalized *Digital Health Twin* for every patient — predicting disease risks before they become critical.

[![Python](https://img.shields.io/badge/Python-3.14.2-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb)](https://reactjs.org)
[![Groq](https://img.shields.io/badge/Groq-openai%2Fgpt--oss--120b-orange)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| 🧬 **Digital Health Twin** | Complete AI-generated patient model with health score |
| 📊 **Disease Risk Engine** | Ensemble ML (XGBoost + RF + LR) for 5 diseases |
| 🤖 **AI Chat Assistant** | Conversational health AI with patient context memory |
| 📄 **Report Analyzer** | OCR → NLP → LLM pipeline for medical documents |
| 🔮 **What-If Simulator** | Real-time lifestyle change impact simulation |
| ⏱️ **Health Timeline** | Interactive playback of health history |
| 🚨 **Emergency Triage** | AI-powered patient prioritization for hospitals |
| 💊 **Recommendations** | Personalized diet, exercise, sleep, stress plans |
| 🔬 **Explainable AI** | SHAP-style feature attribution for all predictions |

---

## 🚀 Quick Start — localhost

### Prerequisites
- Python **3.14.2** ([pyenv](https://github.com/pyenv/pyenv) recommended)
- Node.js **20+**
- Tesseract OCR (`brew install tesseract` / `apt install tesseract-ocr`)
- Groq API key → [console.groq.com](https://console.groq.com)

---

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/meditwin-ai.git
cd meditwin-ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment with Python 3.14.2
python3.14 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → add your GROQ_API_KEY and SECRET_KEY
nano .env
```

**`.env` minimum config:**
```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-120b
SECRET_KEY=your-32-char-secret-here
ALLOWED_ORIGINS=http://localhost:5173
```

```bash
# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: `http://localhost:8000/docs`

---

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## 🐳 Docker Deployment

```bash
# From project root
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

docker compose up --build -d

# Check status
docker compose ps
docker compose logs backend -f
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## ☁️ Cloud Deployment

### Backend → Render

1. Push to GitHub
2. Create new **Web Service** on [Render](https://render.com)
3. Settings:
   - **Environment**: Docker
   - **Root Directory**: `backend/`
   - **Port**: `8000`
4. Add Environment Variables:
   - `GROQ_API_KEY` → your key
   - `SECRET_KEY` → 32-char random string
   - `GROQ_MODEL` → `openai/gpt-oss-120b`
   - `ALLOWED_ORIGINS` → `https://your-app.vercel.app`

### Frontend → Vercel

```bash
cd frontend
npm install -g vercel
vercel --prod

# Set environment variable in Vercel dashboard:
# VITE_API_URL = https://your-backend.onrender.com
```

---

## 🏗️ Architecture

```
meditwin-ai/
├── backend/                    # FastAPI (Python 3.14.2)
│   ├── main.py                 # App entry point + CORS
│   ├── requirements.txt        # All Python dependencies
│   ├── .env.example            # Environment template
│   ├── Dockerfile              # Multi-stage production build
│   ├── routers/
│   │   ├── auth.py             # JWT authentication
│   │   ├── ai.py               # Groq AI endpoints
│   │   ├── health.py           # Vitals & timeline
│   │   ├── reports.py          # OCR → LLM pipeline
│   │   └── triage.py           # Emergency prioritization
│   ├── services/
│   │   ├── groq_service.py     # Groq API (openai/gpt-oss-120b)
│   │   ├── ml_service.py       # Sklearn ensemble models
│   │   └── ocr_service.py      # Tesseract OCR pipeline
│   └── models/
│       └── schemas.py          # Pydantic v2 models
│
├── frontend/                   # React 18 + Vite
│   ├── src/
│   │   ├── App.jsx             # Main app (all 9 pages)
│   │   ├── main.jsx            # Entry point
│   │   └── api.js              # Backend API client
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── Dockerfile
│
├── docker-compose.yml          # Full-stack Docker setup
└── README.md
```

---

## 🧠 AI/ML Pipeline

```
Patient Data
    │
    ▼
Feature Engineering (23 clinical params)
    │
    ├──► XGBoost Classifier ──┐
    ├──► Random Forest ────────►  VotingClassifier (soft)
    └──► Logistic Regression ─┘
              │
              ▼
    Risk Probabilities (5 diseases)
              │
              ▼
    SHAP Feature Attribution
              │
              ▼
    Groq LLM (openai/gpt-oss-120b)
              │
              ▼
    Clinical AI Summary + Recommendations
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Get JWT token |
| `POST` | `/api/v1/ai/health-twin` | Generate Digital Health Twin |
| `POST` | `/api/v1/ai/chat` | AI health conversation |
| `POST` | `/api/v1/ai/whatif` | Lifestyle simulation |
| `POST` | `/api/v1/ai/recommendations` | Personalized plans |
| `POST` | `/api/v1/reports/analyze` | Analyze medical report |
| `POST` | `/api/v1/health/vitals` | Record vitals |
| `GET`  | `/api/v1/health/vitals/live` | Live vitals stream |
| `GET`  | `/api/v1/health/timeline` | Health history |
| `POST` | `/api/v1/triage/admit` | Admit to triage |
| `GET`  | `/api/v1/triage/queue` | Get priority queue |

Full interactive docs: `http://localhost:8000/docs`

---

## 🔒 Security

- JWT tokens with configurable expiry
- bcrypt password hashing (cost factor 12)
- CORS whitelist enforcement
- File upload validation (type + size)
- Non-root Docker user
- No sensitive data in logs

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Recharts, Framer Motion |
| **Backend** | Python 3.14.2, FastAPI 0.115, Uvicorn |
| **AI/LLM** | Groq API (`openai/gpt-oss-120b`) |
| **ML** | Scikit-learn (GBM + RF + LR ensemble) |
| **OCR** | Tesseract + Pillow + pdf2image |
| **Auth** | JWT (python-jose) + bcrypt (passlib) |
| **Validation** | Pydantic v2 |
| **Container** | Docker + Docker Compose |
| **Deployment** | Render (backend) + Vercel (frontend) |

---

## 📜 License

MIT License © 2026 MediTwin AI Team

---

> **MediTwin AI** — *"Not just a student project — this is the future of healthcare."*
