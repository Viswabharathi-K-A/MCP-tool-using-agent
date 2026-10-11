
# Stage 1: Install Python dependencies
FROM python:3.13-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime
FROM python:3.13-slim

WORKDIR /app

# Node.js/npm for Filesystem and Tavily MCP servers
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=builder /install /usr/local

# Copy application files
COPY . .

# Create workspace and non-root user
RUN mkdir -p /app/workspace \
    && useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser

# Writable cache for npx
ENV npm_config_cache=/home/appuser/.npm
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Start FastAPI on the port provided by Cloud Run
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
