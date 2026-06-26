# =============================================================================
# FINESE 2 - AI-Powered Data Intelligence Platform (Flask)
# Multi-stage optimized Docker build for production deployment
# =============================================================================

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (leverage Docker cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    GUNICORN_CMD_ARGS="--bind 0.0.0.0:5000 --workers 2 --threads 2 --timeout 120"

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libcurl4 \
    libxml2 \
    libxslt1.1 \
    libharfbuzz0b \
    libfribidi0 \
    libcairo2 \
    libpango-1.0-0 \
    libjpeg62-turbo \
    libpng16-16 \
    libgdk-pixbuf2.0-0 \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Copy Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p static/uploads static/exports static/reports models flask_session \
    && chmod -R 755 static/ models/ flask_session/

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run with Gunicorn (production WSGI server)
CMD ["gunicorn", "app:app"]