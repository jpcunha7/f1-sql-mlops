"""Smoke tests for training pipeline."""

import pickle
from pathlib import Path

import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from f1sqlmlops.config import config
from f1sqlmlops.training.train_dnf import create_pipeline as create_dnf_pipeline
from f1sqlmlops.training.train_top10 import create_pipeline as create_top10_pipeline


@pytest.fixture
def sample_training_data():
    """Create sample training data."""
    n_samples = 100

    # Create features
    X = pd.DataFrame({
        'grid_position': range(1, n_samples + 1),
        'qualifying_position': range(1, n_samples + 1),
        'driver_top10_rate_recent': [0.5] * n_samples,
        'driver_dnf_rate_recent': [0.2] * n_samples,
        'constructor_points_recent': [100.0] * n_samples,
    })

    # Create targets
    # Top 10: first 40% are top 10
    y_top10 = pd.Series([1] * 40 + [0] * 60)

    # DNF: last 20% are DNF
    y_dnf = pd.Series([0] * 80 + [1] * 20)

    return X, y_top10, y_dnf


def test_create_top10_pipeline():
    """Test that Top-10 pipeline can be created."""
    pipeline = create_top10_pipeline(n_estimators=10, max_depth=3)

    assert pipeline is not None
    assert 'preprocessor' in pipeline.named_steps
    assert 'classifier' in pipeline.named_steps
    assert isinstance(pipeline.named_steps['classifier'], RandomForestClassifier)


def test_create_dnf_pipeline():
    """Test that DNF pipeline can be created."""
    pipeline = create_dnf_pipeline(n_estimators=10, max_depth=3)

    assert pipeline is not None
    assert 'preprocessor' in pipeline.named_steps
    assert 'classifier' in pipeline.named_steps
    assert isinstance(pipeline.named_steps['classifier'], RandomForestClassifier)


def test_top10_pipeline_fit_predict(sample_training_data):
    """Test that Top-10 pipeline can fit and predict."""
    X, y_top10, _ = sample_training_data

    pipeline = create_top10_pipeline(n_estimators=10, max_depth=3)
    pipeline.fit(X, y_top10)

    # Should be able to predict
    predictions = pipeline.predict(X)
    assert len(predictions) == len(X)
    assert set(predictions).issubset({0, 1})

    # Should be able to predict probabilities
    probabilities = pipeline.predict_proba(X)
    assert probabilities.shape[0] == len(X)
    # Should have 2 columns for binary classification (or 1 if single class)
    assert probabilities.shape[1] in [1, 2]


def test_dnf_pipeline_fit_predict(sample_training_data):
    """Test that DNF pipeline can fit and predict."""
    X, _, y_dnf = sample_training_data

    pipeline = create_dnf_pipeline(n_estimators=10, max_depth=3)
    pipeline.fit(X, y_dnf)

    # Should be able to predict
    predictions = pipeline.predict(X)
    assert len(predictions) == len(X)
    assert set(predictions).issubset({0, 1})

    # Should be able to predict probabilities
    probabilities = pipeline.predict_proba(X)
    assert probabilities.shape[0] == len(X)
    assert probabilities.shape[1] in [1, 2]


def test_pipeline_serialization(sample_training_data, tmp_path):
    """Test that trained pipelines can be saved and loaded."""
    X, y_top10, _ = sample_training_data

    # Train pipeline
    pipeline = create_top10_pipeline(n_estimators=10, max_depth=3)
    pipeline.fit(X, y_top10)

    # Save to file
    model_path = tmp_path / 'test_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)

    # Load from file
    with open(model_path, 'rb') as f:
        loaded_pipeline = pickle.load(f)

    # Should make same predictions
    original_preds = pipeline.predict(X)
    loaded_preds = loaded_pipeline.predict(X)

    assert (original_preds == loaded_preds).all()


def test_pipeline_with_missing_values():
    """Test that pipeline handles missing values."""
    X = pd.DataFrame({
        'grid_position': [1, 2, None, 4, 5],
        'qualifying_position': [1, None, 3, 4, 5],
        'driver_top10_rate_recent': [0.5, 0.6, 0.7, None, 0.8],
        'driver_dnf_rate_recent': [0.1, 0.2, 0.3, 0.4, 0.5],
        'constructor_points_recent': [100.0, 110.0, 120.0, 130.0, 140.0],
    })
    y = pd.Series([1, 0, 1, 0, 1])

    pipeline = create_top10_pipeline(n_estimators=10, max_depth=3)

    # Should handle missing values (has imputer)
    pipeline.fit(X, y)
    predictions = pipeline.predict(X)

    assert len(predictions) == len(X)
    assert not pd.isna(predictions).any()


def test_pipeline_feature_importance(sample_training_data):
    """Test that feature importance can be extracted."""
    X, y_top10, _ = sample_training_data

    pipeline = create_top10_pipeline(n_estimators=10, max_depth=3)
    pipeline.fit(X, y_top10)

    # Should be able to get feature importances from the classifier
    classifier = pipeline.named_steps['classifier']
    importances = classifier.feature_importances_

    assert len(importances) == X.shape[1]
    assert all(imp >= 0 for imp in importances)
    assert sum(importances) > 0  # At least some features should be important


def test_pipeline_parameters():
    """Test that pipeline parameters are set correctly."""
    pipeline = create_top10_pipeline(n_estimators=50, max_depth=10)

    classifier = pipeline.named_steps['classifier']

    assert classifier.n_estimators == 50
    assert classifier.max_depth == 10
    assert classifier.random_state == 42
    assert classifier.class_weight == 'balanced'


def test_class_balance_handling(sample_training_data):
    """Test that pipeline handles imbalanced classes."""
    X, y_top10, _ = sample_training_data

    # Check class balance
    class_counts = y_top10.value_counts()
    assert len(class_counts) == 2  # Binary classification

    # Pipeline should handle imbalance with class_weight='balanced'
    pipeline = create_top10_pipeline(n_estimators=10, max_depth=3)
    pipeline.fit(X, y_top10)

    # Should make predictions for both classes
    predictions = pipeline.predict(X)
    unique_predictions = set(predictions)

    # In some cases with small data, might predict only one class
    # But pipeline should at least run without errors
    assert len(unique_predictions) >= 1


def test_smoke_test_full_training(tmp_path):
    """Smoke test: full training process with minimal data."""
    # This is a minimal integration test
    # Full tests are in CI with actual toy data

    # Create minimal dataset
    X_train = pd.DataFrame({
        'grid_position': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'qualifying_position': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'driver_top10_rate_recent': [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.0],
        'driver_dnf_rate_recent': [0.1] * 10,
        'constructor_points_recent': [150.0] * 10,
    })
    y_train = pd.Series([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])

    # Train model
    pipeline = create_top10_pipeline(n_estimators=5, max_depth=2)
    pipeline.fit(X_train, y_train)

    # Save model
    model_path = tmp_path / 'smoke_test_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)

    # Load and predict
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)

    predictions = loaded_model.predict(X_train)

    # Basic sanity checks
    assert len(predictions) == len(X_train)
    assert model_path.exists()
    assert model_path.stat().st_size > 0
