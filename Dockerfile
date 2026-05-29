# ==========================================
# STAGE 1: Builder
# ==========================================
FROM python:3.10-slim AS builder

WORKDIR /app

# Install compiler dependencies needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# Install dependencies into virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# STAGE 2: Production Runner
# ==========================================
FROM python:3.10-slim AS runner

WORKDIR /app

# Install only minimal runtime system dependencies (no build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak \
    libportaudio2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set up environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose production port
EXPOSE 8000

# Create application directories and add non-root user
RUN mkdir -p /app/data /app/models /app/logs && \
    useradd -u 8888 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user for execution security
USER appuser

# Copy codebase
COPY --chown=appuser:appuser . .

# Run FastAPI app with production uvicorn configuration
CMD ["sh", "-c", "uvicorn src.api.main_api:app --host 0.0.0.0 --port $PORT --workers 2 --log-level info"]