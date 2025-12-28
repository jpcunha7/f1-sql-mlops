#!/bin/bash
# Docker validation script

set -e

echo "🏎️  F1 SQL MLOps - Docker Validation"
echo "====================================="

# Check Docker is installed
echo ""
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✓ Docker: $(docker --version)"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo "✓ Docker Compose: $(docker-compose --version)"

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running"
    exit 1
fi
echo "✓ Docker daemon is running"

# Validate Dockerfile
echo ""
echo "Validating Dockerfile..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi
echo "✓ Dockerfile exists"

# Validate docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found"
    exit 1
fi

# Validate docker-compose syntax
if ! docker-compose config > /dev/null 2>&1; then
    echo "❌ docker-compose.yml has syntax errors"
    exit 1
fi
echo "✓ docker-compose.yml is valid"

# Check .dockerignore
if [ ! -f ".dockerignore" ]; then
    echo "⚠️  .dockerignore not found (recommended)"
else
    echo "✓ .dockerignore exists"
fi

# Check required directories
echo ""
echo "Checking project structure..."
for dir in src app dbt; do
    if [ ! -d "$dir" ]; then
        echo "❌ Directory '$dir' not found"
        exit 1
    fi
    echo "✓ $dir/"
done

# Check required files
for file in pyproject.toml README.md Makefile; do
    if [ ! -f "$file" ]; then
        echo "❌ File '$file' not found"
        exit 1
    fi
    echo "✓ $file"
done

echo ""
echo "====================================="
echo "✅ All Docker validations passed!"
echo ""
echo "Next steps:"
echo "  1. Build image:     docker-compose build"
echo "  2. Run pipeline:    docker-compose --profile pipeline up pipeline"
echo "  3. Train models:    docker-compose --profile training up trainer"
echo "  4. Start app:       docker-compose up -d app"
echo "  5. View app:        open http://localhost:8501"
