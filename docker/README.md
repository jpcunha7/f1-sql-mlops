# Docker Quick Reference

Quick commands for Docker deployment.

## Quick Start

```bash
# Build image
docker-compose build

# Run everything
docker-compose --profile pipeline up pipeline    # 1. Generate data
docker-compose --profile training up trainer     # 2. Train models
docker-compose up -d app mlflow                   # 3. Start services

# Access
http://localhost:8501  # Streamlit app
http://localhost:5000  # MLflow UI
```

## Common Commands

### Building

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build app

# Build without cache
docker-compose build --no-cache

# Pull base images
docker-compose pull
```

### Running

```bash
# Start app in background
docker-compose up -d app

# Start with logs
docker-compose up app

# Run all services
docker-compose up -d

# Run specific profiles
docker-compose --profile training up trainer
docker-compose --profile pipeline up pipeline
```

### Monitoring

```bash
# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Resource usage
docker stats f1-predictor-app

# Health check
curl http://localhost:8501/_stcore/health
```

### Debugging

```bash
# Interactive shell
docker-compose exec app bash

# Run command
docker-compose exec app python -m f1sqlmlops.inference.predict --help

# View environment
docker-compose exec app env

# Check files
docker-compose exec app ls -lh /app/models/
```

### Cleanup

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker-compose down -v --rmi all
docker system prune -a
```

## Service Overview

| Service | Port | Purpose | Profile |
|---------|------|---------|---------|
| app | 8501 | Streamlit web app | default |
| mlflow | 5000 | Experiment tracking | default |
| trainer | - | Model training | training |
| pipeline | - | Data generation | pipeline |

## Environment Variables

```bash
# Create .env file
cat > .env <<EOF
DUCKDB_PATH=/app/data/warehouse/warehouse.duckdb
DATA_DIR=/app/data
MODELS_DIR=/app/models
TRAIN_END_YEAR=2016
VAL_YEARS=2017,2018
TEST_YEARS=2019,2020
EOF

# Use it
docker-compose --env-file .env up
```

## Volume Mounts

```
./data       → /app/data       (database, parquet files)
./models     → /app/models     (trained models)
./mlruns     → /app/mlruns     (MLflow artifacts)
./reports    → /app/reports    (evaluation reports)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port in use | Change ports in docker-compose.yml |
| Models not found | Run trainer: `docker-compose --profile training up trainer` |
| No data | Run pipeline: `docker-compose --profile pipeline up pipeline` |
| Out of memory | Increase Docker memory limit |
| Container won't start | Check logs: `docker-compose logs app` |

## Production Deployment

```bash
# Build production image
docker-compose build --no-cache

# Start with restart policy
docker-compose up -d --restart unless-stopped

# Scale app (if needed)
docker-compose up -d --scale app=3

# Update image
docker-compose pull
docker-compose up -d
```

## CI/CD Integration

```yaml
# .github/workflows/docker.yml
name: Docker
on: push
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build
        run: docker-compose build
      - name: Test
        run: docker-compose --profile pipeline up pipeline
```

## See Also

- [Complete Docker Guide](../DOCKER.md)
- [Main README](../README.md)
- [Project Documentation](../docs/)
