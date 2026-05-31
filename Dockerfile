# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENV=production

WORKDIR /app

# Install system dependencies (build tools + ffmpeg for Whisper)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to utilize Docker build cache
COPY requirements.txt .

# Install dependencies (CPU-optimized PyTorch first, then others)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.2.2 --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformer and Whisper models to speed up startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
    python -c "import whisper; whisper.load_model('base')"

# Copy the entire codebase
COPY . .

# Expose server port
EXPOSE 8000

# Set default startup command
CMD ["sh", "-c", "python -m Ashu.seed_gita && uvicorn Ashu.main:app --host 0.0.0.0 --port ${PORT}"]
