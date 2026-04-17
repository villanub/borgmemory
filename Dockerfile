FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source first — hatchling needs it to resolve packages = ["src/borg"]
COPY pyproject.toml .
COPY src/ src/

# Install package + deps
RUN pip install --no-cache-dir .

# Copy remaining assets
COPY migrations/ migrations/

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run — borg is now an installed package, import directly
CMD ["uvicorn", "borg.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
