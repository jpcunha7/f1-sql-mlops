# F1 SQL MLOps - Production Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY app/ ./app/
COPY dbt/ ./dbt/
COPY pyproject.toml README.md ./
COPY Makefile ./

# Create necessary directories
RUN mkdir -p data/warehouse data/raw_parquet data/toy_parquet models reports mlruns

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Environment variables with defaults
ENV DUCKDB_PATH=/app/data/warehouse/warehouse.duckdb
ENV DATA_DIR=/app/data
ENV MODELS_DIR=/app/models
ENV TRAIN_END_YEAR=2016
ENV VAL_YEARS=2017,2018
ENV TEST_YEARS=2019,2020

# Expose Streamlit port
EXPOSE 8501

# Expose MLflow port
EXPOSE 5000

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command: run Streamlit app
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
