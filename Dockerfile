FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch first (replaces the huge GPU version ~2GB -> ~200MB)
RUN pip install --no-cache-dir torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables can be overridden at runtime
ENV PYTHONPATH=/app

# No specific entrypoint here since docker-compose will dictate if this runs as API or Celery worker
