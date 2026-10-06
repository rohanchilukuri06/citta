# ==========================================
# CittaAI Backend — built from the repository root (Railway's default build context).
# Identical to backend/Dockerfile, with paths relative to the repo root, so the deploy works
# whether or not the service's Root Directory is set to "backend".
# ==========================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    ENVIRONMENT=production \
    DEBUG=false \
    VECTOR_DB_PATH=/app/vector_store.db \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch first: the default wheel bundles ~3 GB of CUDA libraries this server never uses
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/ /app

# Build the vector index (and download the embedding model) into the image
RUN python scripts/build_vector_db.py && \
    python -c "import sqlite3; c=sqlite3.connect('/app/vector_store.db'); print('Build-time DB Chunk Count:', c.execute('select count(*) from chunks').fetchone()[0])"

EXPOSE 8000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
