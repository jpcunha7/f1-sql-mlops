# Model Card: Top-10 Finish Classifier

## Model Details

**Model Name:** F1 Top-10 Finish Predictor
**Model Version:** 1.0
**Model Type:** Binary Classification (Random Forest)
**Framework:** scikit-learn
**Date:** 2025-12-28
**License:** MIT

## Intended Use

### Primary Use Case
Predict the probability that a Formula 1 driver will finish in the top 10 positions (scoring points) in an upcoming race, using only information available before the race starts.

### Intended Users
- F1 data analysts
- Racing strategists
- Fantasy F1 players
- Sports betting analysts (for research only)
- Data science portfolio demonstrations

### Out-of-Scope Uses
- Real-time betting decisions (model is trained on historical data through 2020)
- Safety-critical decisions
- Driver performance evaluation for contract decisions

## Training Data

### Data Source
Kaggle: "Formula 1 World Championship (1950-2020)"

### Data Window
- **Training Set:** 1950-2016 (23,380 race results)
- **Validation Set:** 2017-2018 (820 race results)
- **Test Set:** 2019-2020 (760 race results)

### Target Definition
`label_top10 = 1` if driver finished the race AND final position ≤ 10, else `0`

### Leakage Prevention
- Features computed using **only past races** (window functions exclude current race)
- No race result features from the target race (only qualifying and grid position)
- No lap times, pit stops, or in-race data used

## Features

### Pre-Race Features (24 total)
1. **Qualifying Performance:**
   - qualifying_position
   - grid_position

2. **Driver Historical Performance:**
   - driver_career_races
   - driver_career_top10_rate
   - driver_career_dnf_rate
   - driver_career_wins
   - driver_top10_rate_recent (last 5 races)
   - driver_dnf_rate_recent (last 10 races)
   - driver_avg_points_recent
   - driver_avg_positions_gained_recent
   - driver_races_in_window

3. **Constructor (Team) Performance:**
   - constructor_career_entries
   - constructor_career_top10_rate
   - constructor_career_dnf_rate
   - constructor_top10_rate_recent
   - constructor_dnf_rate_recent
   - constructor_avg_points_recent

4. **Circuit-Specific History:**
   - circuit_avg_dnf_rate
   - circuit_times_hosted
   - driver_top10_rate_at_circuit
   - driver_dnf_rate_at_circuit
   - driver_races_at_circuit

5. **Interaction Features:**
   - started_top_5 (boolean)
   - started_top_10 (boolean)

### Most Important Features
1. driver_career_top10_rate (16.4%)
2. grid_position (10.9%)
3. constructor_career_top10_rate (10.3%)
4. driver_avg_points_recent (8.4%)
5. constructor_avg_points_recent (8.0%)

## Model Architecture

**Algorithm:** Random Forest Classifier
**Hyperparameters:**
- n_estimators: 100
- max_depth: 10
- random_state: 42
- class_weight: balanced

**Preprocessing:**
- Numeric features: Median imputation
- No scaling applied (tree-based model)

## Performance Metrics

### Validation Set (2017-2018)
- **Accuracy:** 75.7%
- **ROC-AUC:** 0.836
- **Precision (Top-10):** 0.73
- **Recall (Top-10):** 0.83
- **F1-Score (Top-10):** 0.77

### Class Distribution
- Training: 41.2% top-10 finishes
- Validation: 50.0% top-10 finishes (modern era has more finishers)

## Limitations

1. **Temporal Drift:**
   - Trained on data through 2020
   - F1 regulations changed significantly in 2022 (new technical regulations)
   - Performance on 2022+ races may degrade

2. **Missing Context:**
   - Weather conditions not included
   - Driver changes mid-season not fully captured
   - Technical failures are stochastic and hard to predict

3. **Data Quality:**
   - Early era data (1950s-1970s) has different completion rates
   - Some qualifying data missing (uses grid position as fallback)

4. **Class Imbalance:**
   - Modern era has higher finish rates than historical data
   - Model may be conservative for recent seasons

## Ethical Considerations

- **Fairness:** Model treats all drivers equally based on historical performance
- **Gambling:** Not intended for real-money betting decisions
- **Bias:** Historical data reflects past team resources and driver opportunities

## Monitoring & Maintenance

### Recommended Updates
- Retrain annually with new season data
- Monitor performance metrics on holdout validation sets
- Alert if ROC-AUC drops below 0.75

### Known Issues
- Very low recall for DNF prediction (separate DNF model recommended)
- May overpredict points for backmarker teams in modern era

## How to Use

### Loading the Model
```python
import joblib
model = joblib.load('models/top10_classifier.pkl')
```

### Making Predictions
```python
from f1sqlmlops.inference.predict import load_models, predict_race

models = load_models()
predictions = predict_race(race_data, models, feature_cols)
```

### CLI Usage
```bash
python -m f1sqlmlops.inference.predict --year 2020 --race-id 1031
```

## References

- Dataset: https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020
- MLflow Tracking: `mlruns/` directory
- dbt Documentation: See GitHub Pages deployment

## Contact

For questions or issues, please open a GitHub issue in the repository.

---

**Model Card Template Version:** 1.0
**Last Updated:** 2025-12-28
