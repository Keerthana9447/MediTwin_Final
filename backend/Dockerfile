# ═══════════════════════════════════════════
#  MediTwin AI — Production Dockerfile
#  Python 3.14.2 | FastAPI | Multi-stage
# ═══════════════════════════════════════════

# ── Stage 1: Builder ──────────────────────
FROM python:3.14-slim AS builder

WORKDIR /build

# System dependencies for OCR and ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgomp1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy system libs from builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 meditwin && chown -R meditwin:meditwin /app
USER meditwin

# Create model directory
RUN mkdir -p /app/models/trained

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--no-access-log"]
