# F1 Race Predictor - Streamlit App

Interactive web application for F1 race predictions using machine learning.

## Features

### 🏁 Make Predictions
- Select any race from the historical dataset
- View predictions for all drivers in that race
- See probability scores for:
  - Top-10 finish
  - DNF (Did Not Finish)
- Interactive visualizations
- Real-time accuracy metrics (when ground truth available)

### 📊 Model Performance
- Test set performance metrics
- Year-by-year accuracy breakdown
- Confusion matrices for both models
- Performance trends over time

### 🔍 Feature Importance
- Top 15 most important features for each model
- Feature importance visualizations
- Detailed feature descriptions
- Full feature rankings

### 📈 Historical Analysis
- Dataset overview and statistics
- Train/validation/test split breakdown
- Historical trends (top-10 rates, DNF rates)
- Feature distribution analysis

## Running the App

### Local Development

```bash
# Ensure you're in the project root
cd /path/to/f1-sql-mlops

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Set environment variables
export DUCKDB_PATH=./data/warehouse/warehouse.duckdb

# Run Streamlit
streamlit run app/streamlit_app.py
```

The app will open in your browser at http://localhost:8501

### With Make

```bash
make app
```

## Requirements

The app requires:
- Trained models in `models/` directory
  - `top10_classifier.pkl`
  - `dnf_classifier.pkl`
  - Feature lists (`.txt` files)
- DuckDB warehouse with dbt models built
- Python packages:
  - streamlit
  - plotly
  - pandas
  - scikit-learn

## App Structure

```
app/
├── streamlit_app.py       # Main application
├── README.md              # This file
└── __init__.py
```

## Screenshots

### Predictions Page
- Interactive race selector
- Driver-by-driver predictions
- Probability visualizations
- Accuracy metrics

### Performance Page
- Overall model metrics
- Year-by-year breakdown
- Confusion matrices
- Performance trends

### Feature Importance
- Bar charts of top features
- Complete feature rankings
- Feature descriptions

### Historical Analysis
- Dataset statistics
- Temporal split visualization
- Historical trends
- Feature distributions

## Configuration

The app uses configuration from `src/f1sqlmlops/config.py`:
- `DUCKDB_PATH`: Database location
- `MODELS_DIR`: Trained models directory
- `TRAIN_END_YEAR`: Training cutoff
- `VAL_YEARS`: Validation years
- `TEST_YEARS`: Test years

## Troubleshooting

### Models not found
Ensure you've run training:
```bash
make train
```

### Data not available
Build dbt models first:
```bash
make dbt-build
```

### Port already in use
Specify a different port:
```bash
streamlit run app/streamlit_app.py --server.port 8502
```

## Deployment

For production deployment, consider:
- Streamlit Cloud (free tier available)
- Docker container
- AWS/GCP/Azure app services

See `docker/` directory for containerization options.
