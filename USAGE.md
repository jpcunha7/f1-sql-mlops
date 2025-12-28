# Data Ingestion Usage Guide

## Overview

The data ingestion pipeline downloads F1 data from Kaggle, converts it to Parquet format, and validates schemas.

## Setup

1. Get Kaggle API credentials:
   - Go to https://www.kaggle.com/settings/account
   - Click "Create New API Token"
   - Save the downloaded `kaggle.json` file

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add:
# KAGGLE_USERNAME=your_username
# KAGGLE_KEY=your_key_from_kaggle.json
```

3. Install dependencies:
```bash
make setup
source venv/bin/activate
```

## Running the Pipeline

### Option 1: One Command (Recommended)
```bash
make ingest
```

This runs:
1. Download from Kaggle
2. Convert CSV to Parquet
3. Validate schemas

### Option 2: Step by Step

1. Download data from Kaggle:
```bash
python -m f1sqlmlops.ingestion.kaggle_download
```

Output: CSV files in `data/raw/`

2. Convert to Parquet:
```bash
python -m f1sqlmlops.ingestion.csv_to_parquet
```

Output: Parquet files in `data/raw_parquet/`

3. Validate schemas:
```bash
python -m f1sqlmlops.quality.schema_checks
```

## Generating Toy Data (for CI/CD)

For testing without Kaggle credentials:

```bash
python -m f1sqlmlops.ingestion.generate_toy_data --output-dir data/toy_parquet
```

This creates a small synthetic dataset that matches the schema of the real data.

## CLI Options

### kaggle_download.py
```bash
python -m f1sqlmlops.ingestion.kaggle_download --help

Options:
  --force    Re-download even if files exist
```

### csv_to_parquet.py
```bash
python -m f1sqlmlops.ingestion.csv_to_parquet --help

Options:
  --raw-dir DIRECTORY       Source CSV directory
  --parquet-dir DIRECTORY   Output Parquet directory
```

### schema_checks.py
```bash
python -m f1sqlmlops.ingestion.schema_checks --help

Options:
  --parquet-dir DIRECTORY   Directory to validate
```

### generate_toy_data.py
```bash
python -m f1sqlmlops.ingestion.generate_toy_data --help

Options:
  --output-dir DIRECTORY    Where to save toy data
```

## Expected Data

After running `make ingest`, you should have:

```
data/
├── raw/                    # CSV files (not in git)
│   ├── races.csv
│   ├── results.csv
│   ├── drivers.csv
│   ├── constructors.csv
│   ├── circuits.csv
│   ├── qualifying.csv
│   ├── status.csv
│   └── ... (more files)
├── raw_parquet/           # Parquet files (not in git)
│   ├── races.parquet
│   ├── results.parquet
│   └── ... (all tables)
└── toy_parquet/           # Synthetic data (in git)
    └── ... (small dataset for CI)
```

## Troubleshooting

### "Kaggle credentials not found"
- Make sure `.env` file exists with KAGGLE_USERNAME and KAGGLE_KEY
- Source your environment: `source venv/bin/activate`

### "No CSV files found"
- Run `make ingest` or the kaggle_download step first

### "Schema validation failed"
- The downloaded dataset might have changed
- Check the REQUIRED_SCHEMAS in `schema_checks.py`
- Update if necessary

## Next Steps

After successful ingestion:

1. Build dbt warehouse: `make dbt-build`
2. Export features: `make features`
3. Train models: `make train`

See main README.md for complete pipeline documentation.
