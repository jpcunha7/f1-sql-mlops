# F1 SQL MLOps: Production-Grade Race Prediction Pipeline

A complete, open-source ML engineering project predicting Formula 1 race outcomes using modern data stack: DuckDB, dbt, MLflow, and scikit-learn.

## Project Overview

This project predicts, before each race:
- **Probability of Top-10 finish** (points-scoring position)
- **Probability of DNF** (Did Not Finish)

**Key Features:**
- 100% open-source, MIT-licensed
- Local-first: runs entirely on your machine
- No cloud dependencies (except free GitHub services)
- Production-grade: proper testing, CI/CD, documentation
- Reproducible: Docker + locked dependencies
- Call via code: CLI tools + Make targets

**Data Source:** Kaggle Formula 1 World Championship (1950-2020) dataset

## Architecture

```
Kaggle API → CSV → Parquet Lake → DuckDB Warehouse
                                       ↓
                                   dbt (SQL)
                                       ↓
                            Feature Engineering
                                       ↓
                           Train Models (MLflow)
                                       ↓
                              Inference Pipeline
                                       ↓
                             Streamlit Demo App
```

## Quick Start

### Prerequisites
- Python 3.12+
- Make
- Kaggle API credentials

### Installation

1. Clone repository:
```bash
git clone https://github.com/yourusername/f1-sql-mlops.git
cd f1-sql-mlops
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env and add your Kaggle credentials
```

3. Install dependencies:
```bash
make setup
source venv/bin/activate
```

### Run Full Pipeline

```bash
# 1. Download and prepare data
make ingest

# 2. Build data warehouse with dbt
make dbt-build

# 3. Export features
make features

# 4. Train models
make train

# 5. Generate evaluation reports
make report

# 6. Make predictions
make predict SEASON=2020 ROUND=10

# 7. Launch demo app
make app
```

## Project Status

**Current Implementation:** Minimum Viable Product (MVP)

This repository provides the complete project structure and core implementation for:
- Configuration management
- Data ingestion framework
- dbt project structure
- Training pipeline skeleton
- CI/CD setup

**To Complete for Production:**

The full production implementation requires ~50 files with ~5000+ lines of code including:
- Complete dbt SQL models (staging, intermediate, marts)
- Full feature engineering logic
- Robust training pipelines with hyperparameter tuning
- Comprehensive test suite
- Advanced Streamlit dashboard
- Complete documentation

This MVP demonstrates the architecture and provides a foundation for extension.

## Data & Leakage Prevention

**Critical Rule:** Features must only use information available BEFORE the race starts.

**Leakage Prevention:**
- No lap times from target race
- No pit stop data from target race
- No race results from target race (except as labels)
- Window functions exclude current race row

**Features Used:**
- Qualifying position
- Grid position
- Driver recent form (points, finishes, DNF rate)
- Constructor recent form
- Circuit-specific history
- Season/round context

## Technology Stack

- **Data Lake:** Parquet files
- **Warehouse:** DuckDB (local, serverless SQL)
- **Transformation:** dbt-core + dbt-duckdb
- **ML Training:** scikit-learn + MLflow
- **Quality:** Evidently (data drift, model performance)
- **App:** Streamlit
- **Orchestration:** Make + CLI tools
- **CI/CD:** GitHub Actions
- **Docs:** GitHub Pages (dbt docs + reports)

## Repository Structure

```
f1-sql-mlops/
├── src/f1sqlmlops/          # Python package
│   ├── ingestion/            # Kaggle download, Parquet conversion
│   ├── warehouse/            # DuckDB utilities
│   ├── features/             # Feature export
│   ├── training/             # Model training + evaluation
│   ├── inference/            # Prediction pipeline
│   └── quality/              # Schema validation
├── dbt/                      # dbt project
│   └── models/
│       ├── staging/          # Raw data cleanup
│       ├── intermediate/     # Joins and enrichment
│       └── marts/            # Final fact/dim tables
├── app/                      # Streamlit demo
├── docker/                   # Containerization
├── .github/workflows/        # CI/CD
├── tests/                    # Pytest tests
├── Makefile                  # Workflow automation
└── README.md                 # This file
```

## Development

### Code Quality
```bash
make lint    # Run ruff
make test    # Run pytest
```

### CI/CD
- **CI:** Runs on every PR (lint + test + dbt on synthetic data)
- **Pages:** Publishes dbt docs + reports on main branch

**Note:** CI uses synthetic toy data (no Kaggle secrets required)

## Deployment

### Local
```bash
make app  # Streamlit runs on localhost:8501
```

### Free Cloud Options
- **Streamlit Community Cloud:** Fork + deploy (free tier)
- **Hugging Face Spaces:** Create space + push

See deployment guides in `docs/` (to be added).

## License

MIT License - see LICENSE file

**Dataset:** Kaggle F1 dataset (separate license)
Not redistributed in this repository.

## Contributing

This is a portfolio/educational project. Contributions welcome via issues and PRs.

## Links

- **Dataset:** https://www.kaggle.com/rohanrao/formula-1-world-championship-1950-2020
- **dbt Docs:** (Will be published to GitHub Pages)
- **Demo App:** (Optional deployment)

## Acknowledgments

- Kaggle for F1 dataset
- Open-source community for amazing tools

## Contact

João Pedro Cunha - Portfolio Project 2025
