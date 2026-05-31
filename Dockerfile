# Dockerfile — Production-ready for Railway
FROM python:3.11-slim

# =====================================
# Environment Variables
# =====================================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENV=production

# Disable HuggingFace progress bars in logs
ENV HF_HUB_DISABLE_PROGRESS_BARS=1
# Use CPU-only torch (no CUDA on Railway)
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

WORKDIR /app

# =====================================
# System Dependencies
# =====================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# =====================================
# Python Dependencies
# (Install CPU PyTorch first to avoid huge CUDA download)
# =====================================
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.2.2 --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-build-isolation openai-whisper==20231117

# =====================================
# Copy Source Code
# =====================================
COPY . .

# =====================================
# Expose Port
# =====================================
EXPOSE 8000

# =====================================
# Startup Command
# Seeds DB on first run (idempotent — skips if already seeded)
# Uvicorn binds to Railway's $PORT (falls back to 8000)
# =====================================
CMD ["sh", "-c", "python -m Ashu.seed_gita && uvicorn Ashu.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
