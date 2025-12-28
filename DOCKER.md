# Docker Deployment Guide

Complete guide for running F1 SQL MLOps in Docker containers.

## Table of Contents
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Services](#services)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB free disk space

### Run the App (Default)

```bash
# Build and start the Streamlit app
docker-compose up -d app

# View logs
docker-compose logs -f app

# Access the app
open http://localhost:8501
```

### Full Pipeline (One-Time Setup)

```bash
# 1. Generate toy data and build dbt models
docker-compose --profile pipeline up pipeline

# 2. Train models
docker-compose --profile training up trainer

# 3. Start the app
docker-compose up -d app
```

## Architecture

The Docker setup uses a **multi-stage build** for optimized images:

```
Stage 1 (Builder)
├── Install build dependencies
├── Compile Python packages
└── Create wheels

Stage 2 (Runtime)
├── Copy compiled packages
├── Install runtime dependencies only
└── Configure application
```

**Benefits:**
- Smaller image size (~500MB vs ~1.5GB)
- Faster container startup
- Reduced attack surface

## Services

### 1. App Service (Streamlit)

**Purpose:** Interactive web application for predictions

```bash
docker-compose up -d app
```

**Access:** http://localhost:8501

**Endpoints:**
- Main app: http://localhost:8501
- Health check: http://localhost:8501/_stcore/health

**Volumes:**
- `./data:/app/data` - Persistent data
- `./models:/app/models` - Trained models
- `./mlruns:/app/mlruns` - MLflow artifacts
- `./reports:/app/reports` - Generated reports

### 2. MLflow Service (Optional)

**Purpose:** Experiment tracking and model registry

```bash
docker-compose up -d mlflow
```

**Access:** http://localhost:5000

**Features:**
- View training runs
- Compare model metrics
- Download artifacts
- Model versioning

### 3. Trainer Service (One-Time)

**Purpose:** Train both prediction models

```bash
docker-compose --profile training up trainer
```

**What it does:**
1. Loads features from DuckDB
2. Trains Top-10 classifier
3. Trains DNF classifier
4. Evaluates on test set
5. Saves models to `./models/`

**Output:**
- `models/top10_classifier.pkl`
- `models/dnf_classifier.pkl`
- `models/*_feature_importance.csv`

### 4. Pipeline Service (One-Time)

**Purpose:** Generate data and build dbt models

```bash
docker-compose --profile pipeline up pipeline
```

**What it does:**
1. Generates toy dataset (7 seasons)
2. Registers Parquet views in DuckDB
3. Runs dbt models
4. Executes dbt tests

**Output:**
- `data/toy_parquet/*.parquet`
- `data/warehouse/warehouse.duckdb`

## Usage Examples

### Complete First-Time Setup

```bash
# 1. Build images
docker-compose build

# 2. Run data pipeline
docker-compose --profile pipeline up pipeline

# 3. Train models
docker-compose --profile training up trainer

# 4. Start app and MLflow
docker-compose up -d app mlflow

# 5. View logs
docker-compose logs -f

# 6. Open browser
open http://localhost:8501
open http://localhost:5000
```

### Development Workflow

```bash
# Start with live code reloading
docker-compose up app

# Rebuild after code changes
docker-compose up --build app

# Run specific command
docker-compose run --rm app python -m f1sqlmlops.inference.predict --help
```

### Production Deployment

```bash
# Build optimized images
docker-compose build --no-cache

# Start in detached mode
docker-compose up -d app

# Enable auto-restart
docker-compose up -d --restart unless-stopped app

# View resource usage
docker stats f1-predictor-app

# Scale (if needed)
docker-compose up -d --scale app=3
```

### Running Commands Inside Container

```bash
# Interactive shell
docker-compose exec app bash

# Run prediction
docker-compose exec app python -m f1sqlmlops.inference.predict \
  --from-db --year 2020 --summary

# Run evaluation
docker-compose exec app python -m f1sqlmlops.training.evaluate

# Check dbt models
docker-compose exec app sh -c "cd dbt && dbt list"
```

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Database
DUCKDB_PATH=/app/data/warehouse/warehouse.duckdb

# Data directories
DATA_DIR=/app/data
MODELS_DIR=/app/models

# Temporal splits
TRAIN_END_YEAR=2016
VAL_YEARS=2017,2018
TEST_YEARS=2019,2020

# Kaggle credentials (optional)
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# Streamlit config
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

Then run:
```bash
docker-compose --env-file .env up
```

### Custom Ports

Edit `docker-compose.yml`:

```yaml
services:
  app:
    ports:
      - "8080:8501"  # Change 8080 to your desired port
```

### Resource Limits

Add to service definition:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## Troubleshooting

### App Won't Start

**Check logs:**
```bash
docker-compose logs app
```

**Common issues:**
- Missing models: Run trainer first
- No data: Run pipeline first
- Port conflict: Change port in docker-compose.yml

### Models Not Found

```bash
# Check if models exist
docker-compose exec app ls -lh /app/models/

# Retrain if missing
docker-compose --profile training up trainer
```

### DuckDB File Locked

```bash
# Stop all containers
docker-compose down

# Remove lock file
rm data/warehouse/warehouse.duckdb.wal

# Restart
docker-compose up app
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory

# Or add memory limit to service
```

### Rebuild from Scratch

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clear Docker cache
docker system prune -a

# Rebuild
docker-compose build --no-cache
docker-compose --profile pipeline up pipeline
docker-compose --profile training up trainer
docker-compose up -d app
```

### Permission Issues

```bash
# Fix ownership (Linux)
sudo chown -R $USER:$USER data/ models/ mlruns/

# Run as current user
docker-compose run --user $(id -u):$(id -g) app <command>
```

## Advanced Usage

### Using Real Kaggle Data

```bash
# 1. Set Kaggle credentials in .env
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# 2. Download data
docker-compose run --rm app python -m f1sqlmlops.ingestion.kaggle_download

# 3. Convert to Parquet
docker-compose run --rm app python -m f1sqlmlops.ingestion.csv_to_parquet

# 4. Rebuild dbt models
docker-compose run --rm app sh -c "cd dbt && dbt build"

# 5. Retrain models
docker-compose --profile training up trainer
```

### CI/CD Integration

**GitHub Actions example:**

```yaml
name: Docker Build
on: push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker-compose build

      - name: Run tests
        run: docker-compose run --rm app pytest tests/

      - name: Run pipeline
        run: docker-compose --profile pipeline up pipeline

      - name: Train models
        run: docker-compose --profile training up trainer
```

### Health Monitoring

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect f1-predictor-app | jq '.[0].State.Health'

# Custom health check endpoint
curl http://localhost:8501/_stcore/health
```

## Image Size Optimization

**Current image:** ~500MB (multi-stage)
**Single-stage:** ~1.5GB

**Further optimization:**
- Use `python:3.11-alpine` (saves 100MB)
- Remove unused dependencies
- Compress layers with `docker-squash`

## Security Best Practices

1. **Don't commit secrets:** Use `.env` files
2. **Run as non-root:** Add `USER` directive
3. **Scan for vulnerabilities:** `docker scan f1-sql-mlops`
4. **Keep base image updated:** Regular rebuilds
5. **Limit network exposure:** Use internal networks

## Performance Tips

1. **Use volumes for data:** Faster I/O than COPY
2. **Enable BuildKit:** `DOCKER_BUILDKIT=1`
3. **Multi-stage builds:** Smaller images
4. **Layer caching:** Order Dockerfile by change frequency
5. **Health checks:** Ensure service readiness

## Deployment Platforms

### Docker Hub

```bash
docker tag f1-sql-mlops:latest your-username/f1-predictor:latest
docker push your-username/f1-predictor:latest
```

### AWS ECS

```bash
aws ecr create-repository --repository-name f1-predictor
docker tag f1-sql-mlops:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/f1-predictor:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/f1-predictor:latest
```

### Google Cloud Run

```bash
gcloud builds submit --tag gcr.io/project-id/f1-predictor
gcloud run deploy --image gcr.io/project-id/f1-predictor --platform managed
```

### Heroku

```bash
heroku container:push web
heroku container:release web
```

## Support

For issues, see the [main README](README.md) or file an issue on GitHub.
