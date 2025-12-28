.PHONY: help setup ingest dbt-build features train report predict app lint test clean

help:
	@echo "F1 SQL MLOps - Make targets:"
	@echo "  make setup        - Create venv and install dependencies"
	@echo "  make ingest       - Download Kaggle data and convert to Parquet"
	@echo "  make dbt-build    - Run dbt models and tests"
	@echo "  make features     - Export feature table"
	@echo "  make train        - Train both models (Top10 + DNF)"
	@echo "  make report       - Generate Evidently reports"
	@echo "  make predict      - Run inference (use SEASON=YYYY ROUND=N)"
	@echo "  make app          - Launch Streamlit demo"
	@echo "  make lint         - Run ruff linter"
	@echo "  make test         - Run pytest"
	@echo "  make clean        - Remove cache and artifacts"

setup:
	python3.12 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -e ".[dev]"
	@echo "Setup complete. Activate with: source venv/bin/activate"

ingest:
	./venv/bin/python -m f1sqlmlops.ingestion.kaggle_download
	./venv/bin/python -m f1sqlmlops.ingestion.csv_to_parquet
	./venv/bin/python -m f1sqlmlops.quality.schema_checks

dbt-build:
	cd dbt && ../venv/bin/dbt deps
	cd dbt && ../venv/bin/dbt run
	cd dbt && ../venv/bin/dbt test

features:
	./venv/bin/python -m f1sqlmlops.features.export_features

train:
	./venv/bin/python -m f1sqlmlops.training.train_top10
	./venv/bin/python -m f1sqlmlops.training.train_dnf

report:
	./venv/bin/python -m f1sqlmlops.training.evaluate

predict:
	@if [ -z "$(SEASON)" ] || [ -z "$(ROUND)" ]; then \
		echo "Usage: make predict SEASON=2020 ROUND=10"; \
		exit 1; \
	fi
	./venv/bin/python -m f1sqlmlops.inference.predict --season $(SEASON) --round $(ROUND)

app:
	./venv/bin/streamlit run app/streamlit_app.py

lint:
	./venv/bin/ruff check src/ tests/

test:
	./venv/bin/pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
	@echo "Cache cleaned (data and models preserved)"
