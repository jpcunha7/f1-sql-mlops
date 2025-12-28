#!/bin/bash
# Launch script for F1 Streamlit app

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment if exists
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Set environment variables
export DUCKDB_PATH="${DUCKDB_PATH:-$PROJECT_ROOT/data/warehouse/warehouse.duckdb}"

# Navigate to project root
cd "$PROJECT_ROOT"

# Run Streamlit
echo "🏎️  Starting F1 Race Predictor..."
echo "📍 DuckDB: $DUCKDB_PATH"
echo ""

streamlit run app/streamlit_app.py \
    --server.headless false \
    --browser.gatherUsageStats false \
    "$@"
