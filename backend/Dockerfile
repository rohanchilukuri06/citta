# ==========================================
# CittaAI Backend Production Dockerfile
# ==========================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENVIRONMENT=production \
    DEBUG=false \
    VECTOR_DB_PATH=/app/vector_store.db \
    PYTHONPATH=/app \
    MALLOC_ARENA_MAX=2 \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2 \
    TOKENIZERS_PARALLELISM=false
# (the last four keep memory within small 1 GB containers: fewer allocator arenas, thread pools sized to the vCPUs)

WORKDIR /app

# Install system dependencies required for C extensions & runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to optimize Docker layer caching
COPY requirements.txt /app/requirements.txt

# CPU-only PyTorch first: the default wheel bundles ~3 GB of CUDA libraries this server never uses
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY . /app

# Build offline vector database during Docker container build phase (Content-Hash Gated)
RUN python scripts/build_vector_db.py

# Verify build-time vector database artifact & print chunk count
RUN ls -lh /app/vector_store.db && \
    python -c "import sqlite3; conn=sqlite3.connect('/app/vector_store.db'); print('Build-time DB Chunk Count:', conn.execute('select count(*) from chunks').fetchone()[0]); conn.close()"

# Expose default backend port
EXPOSE 8000

# Start Uvicorn ASGI server respecting Railway's PORT environment variable
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
