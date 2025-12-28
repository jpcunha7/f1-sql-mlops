# Model Card: DNF (Did Not Finish) Classifier

## Model Details

**Model Name:** F1 DNF Risk Predictor
**Model Version:** 1.0
**Model Type:** Binary Classification (Random Forest)
**Framework:** scikit-learn
**Date:** 2025-12-28
**License:** MIT

## Intended Use

### Primary Use Case
Predict the probability that a Formula 1 driver will fail to finish (DNF) an upcoming race due to mechanical failure, accident, or other issues, using only information available before the race starts.

### Intended Users
- F1 data analysts
- Racing strategists
- Reliability engineers
- Fantasy F1 players
- Data science portfolio demonstrations

### Out-of-Scope Uses
- Safety-critical decisions
- Real-time race strategy (model is pre-race only)
- Driver or team liability assessment

## Training Data

### Data Source
Kaggle: "Formula 1 World Championship (1950-2020)"

### Data Window
- **Training Set:** 1950-2016 (23,380 race results)
- **Validation Set:** 2017-2018 (820 race results)
- **Test Set:** 2019-2020 (760 race results)

### Target Definition
`label_dnf = 1` if driver did NOT finish the race (any status except "Finished" or "+N Laps"), else `0`

### Leakage Prevention
- Features computed using **only past races** (window functions exclude current race)
- No race result features from the target race (only qualifying and grid position)
- No lap times, pit stops, or in-race data used

## Features

### Pre-Race Features (24 total)
1. **Qualifying Performance:**
   - qualifying_position
   - grid_position

2. **Driver Historical Reliability:**
   - driver_career_races
   - driver_career_top10_rate
   - driver_career_dnf_rate ⭐
   - driver_career_wins
   - driver_top10_rate_recent
   - driver_dnf_rate_recent ⭐
   - driver_avg_points_recent
   - driver_avg_positions_gained_recent
   - driver_races_in_window

3. **Constructor (Team) Reliability:**
   - constructor_career_entries
   - constructor_career_top10_rate
   - constructor_career_dnf_rate ⭐
   - constructor_top10_rate_recent
   - constructor_dnf_rate_recent ⭐
   - constructor_avg_points_recent

4. **Circuit-Specific Factors:**
   - circuit_avg_dnf_rate ⭐
   - circuit_times_hosted
   - driver_top10_rate_at_circuit
   - driver_dnf_rate_at_circuit
   - driver_races_at_circuit

5. **Interaction Features:**
   - started_top_5 (boolean)
   - started_top_10 (boolean)

⭐ = Particularly important for DNF prediction

### Most Important Features
1. driver_career_dnf_rate (18.3%)
2. grid_position (14.4%)
3. constructor_career_dnf_rate (9.1%)
4. constructor_dnf_rate_recent (6.7%)
5. driver_dnf_rate_recent (6.2%)

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
- **Accuracy:** 78.3%
- **ROC-AUC:** 0.609
- **Precision (DNF):** 1.00
- **Recall (DNF):** 0.01 ⚠️
- **F1-Score (DNF):** 0.02 ⚠️

### Class Distribution
- Training: 47.3% DNF rate (historical era)
- Validation: 22.0% DNF rate (modern era - much more reliable)

⚠️ **Important:** The model is very conservative in predicting DNFs, with very low recall.

## Limitations

### Critical Limitations

1. **Low Recall:**
   - Model predicts DNF very rarely (high precision, low recall)
   - This is due to severe class imbalance and temporal shift
   - Better at ranking DNF risk than absolute probability

2. **Temporal Reliability Improvement:**
   - Historical F1 (1950s-1980s): ~50-60% DNF rates
   - Modern F1 (2010s-2020s): ~15-25% DNF rates
   - Model trained on mixed eras struggles with modern reliability

3. **Unpredictable Events:**
   - Racing incidents are inherently stochastic
   - Weather-related crashes not captured in features
   - Safety car deployments affect risk

4. **Missing Context:**
   - No engine/gearbox penalty information
   - No practice/FP session crash data
   - No tire compound selection

## Ethical Considerations

- **Risk Assessment:** DNF predictions should not influence driver safety decisions
- **Team Reputation:** Model should not be used to unfairly assess team reliability without context
- **Insurance:** Not validated for risk assessment in insurance contexts

## Use Cases & Recommendations

### Recommended Use
- **Relative Risk Ranking:** Compare drivers within the same race
- **Historical Analysis:** Study reliability trends over eras
- **Feature Importance:** Understand what factors correlate with DNF risk

### Not Recommended
- **Absolute Probabilities:** Do not treat predicted probabilities as true likelihoods
- **Modern Era Only:** Model performs poorly on modern data (low DNF rates)

## Monitoring & Maintenance

### Recommended Improvements
1. **Era-Specific Models:** Train separate models for different F1 eras
2. **Recalibration:** Use isotonic regression to calibrate probabilities
3. **SMOTE/Resampling:** Address class imbalance in modern era
4. **Additional Features:** Include engine penalties, FP crashes

### Known Issues
- Very low recall (0.01) - model almost never predicts DNF
- ROC-AUC of 0.609 indicates weak discrimination
- May need threshold tuning or cost-sensitive learning

## How to Use

### Loading the Model
```python
import joblib
model = joblib.load('models/dnf_classifier.pkl')
```

### Making Predictions
```python
from f1sqlmlops.inference.predict import load_models, predict_race

models = load_models()
predictions = predict_race(race_data, models, feature_cols)

# For DNF risk, use probability as relative ranking
predictions = predictions.sort_values('dnf_probability', ascending=False)
```

### CLI Usage
```bash
python -m f1sqlmlops.inference.predict --year 2020 --race-id 1031
```

### Interpretation Guidance
- **High DNF Probability (>30%):** Driver/team has concerning historical reliability
- **Medium (15-30%):** Average risk for the era
- **Low (<15%):** Strong reliability record

Note: Use probabilities for **ranking** within a race, not as absolute predictions.

## Comparison with Top-10 Model

| Metric | Top-10 Model | DNF Model |
|--------|-------------|-----------|
| Validation Accuracy | 75.7% | 78.3% |
| ROC-AUC | 0.836 | 0.609 |
| Recall | 0.83 | 0.01 ⚠️ |
| Use Case | Points prediction | Risk ranking |

The DNF model is significantly weaker and should be improved or replaced with an era-specific approach.

## References

- Dataset: https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020
- MLflow Tracking: `mlruns/` directory
- dbt Documentation: See GitHub Pages deployment

## Contact

For questions or issues, please open a GitHub issue in the repository.

---

**Model Card Template Version:** 1.0
**Last Updated:** 2025-12-28
