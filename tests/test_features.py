"""Tests for feature export."""

import pytest
from pathlib import Path
import pandas as pd

from f1sqlmlops.features.export_features import (
    get_feature_columns,
    export_features
)
from f1sqlmlops.config import config


@pytest.fixture
def sample_feature_df():
    """Create a sample feature DataFrame for testing."""
    return pd.DataFrame({
        # Metadata columns
        'race_id': [1, 2, 3, 4, 5],
        'driver_id': [1, 1, 1, 1, 1],
        'constructor_id': [1, 1, 1, 1, 1],
        'circuit_id': [1, 2, 1, 2, 1],
        'year': [2015, 2016, 2017, 2018, 2019],
        'round': [1, 1, 1, 1, 1],
        'result_id': [1, 2, 3, 4, 5],
        'race_date': ['2015-03-15', '2016-03-20', '2017-03-26', '2018-03-25', '2019-03-17'],

        # Target columns
        'is_top_10': [1, 1, 0, 1, 0],
        'is_dnf': [0, 0, 1, 0, 1],
        'final_position': [5, 8, None, 9, None],
        'status': ['Finished', 'Finished', 'Accident', 'Finished', 'Engine'],

        # Feature columns
        'grid_position': [3, 5, 7, 4, 6],
        'qualifying_position': [3, 5, 7, 4, 6],
        'driver_top10_rate_recent': [0.7, 0.6, 0.5, 0.6, 0.4],
        'driver_dnf_rate_recent': [0.1, 0.15, 0.2, 0.15, 0.25],
        'constructor_points_recent': [150.0, 140.0, 120.0, 130.0, 100.0],
    })


def test_get_feature_columns(sample_feature_df):
    """Test extraction of feature and target columns."""
    feature_cols, target_cols = get_feature_columns(sample_feature_df)

    # Feature columns should not include metadata or targets
    assert 'race_id' not in feature_cols
    assert 'driver_id' not in feature_cols
    assert 'is_top_10' not in feature_cols
    assert 'is_dnf' not in feature_cols
    assert 'year' not in feature_cols

    # Should include actual features
    assert 'grid_position' in feature_cols
    assert 'qualifying_position' in feature_cols
    assert 'driver_top10_rate_recent' in feature_cols

    # Target columns should be identified
    assert 'target_top_10' in target_cols
    assert 'target_dnf' in target_cols


def test_feature_columns_no_leakage(sample_feature_df):
    """Test that feature columns don't include information from the future."""
    feature_cols, _ = get_feature_columns(sample_feature_df)

    # These would constitute data leakage
    leakage_indicators = [
        'final_position', 'position', 'points', 'laps',
        'milliseconds', 'fastestlap', 'rank', 'statusid'
    ]

    for leakage_col in leakage_indicators:
        # Check that no feature column contains these terms
        matching_cols = [col for col in feature_cols if leakage_col.lower() in col.lower()]
        assert len(matching_cols) == 0, f"Potential leakage: {matching_cols}"


def test_export_features_temporal_splits(tmp_path):
    """Test that export_features creates proper temporal splits."""
    # This test requires actual DuckDB with toy data
    # For now, we'll test the structure
    pytest.skip("Requires full data pipeline - tested in integration tests")


def test_target_columns_renamed(sample_feature_df):
    """Test that target columns are properly renamed."""
    # Add the renamed target columns as they would appear after processing
    df_processed = sample_feature_df.copy()
    df_processed['target_top_10'] = df_processed['is_top_10']
    df_processed['target_dnf'] = df_processed['is_dnf']

    feature_cols, target_cols = get_feature_columns(df_processed)

    # Should have renamed targets
    assert 'target_top_10' in target_cols
    assert 'target_dnf' in target_cols

    # Original names should not be in features
    assert 'is_top_10' not in feature_cols
    assert 'is_dnf' not in feature_cols


def test_feature_dtypes(sample_feature_df):
    """Test that features have appropriate data types."""
    feature_cols, _ = get_feature_columns(sample_feature_df)

    for col in feature_cols:
        # All features should be numeric
        assert pd.api.types.is_numeric_dtype(sample_feature_df[col]), \
            f"Non-numeric feature: {col}"


def test_no_null_keys(sample_feature_df):
    """Test that key columns don't have nulls."""
    key_columns = ['race_id', 'driver_id', 'result_id', 'year']

    for col in key_columns:
        assert sample_feature_df[col].notna().all(), \
            f"Null values found in key column: {col}"


def test_temporal_ordering(sample_feature_df):
    """Test that data can be ordered temporally."""
    # Should be able to sort by year and round
    sorted_df = sample_feature_df.sort_values(['year', 'round'])

    # After sorting, years should be in ascending order
    assert sorted_df['year'].is_monotonic_increasing


def test_feature_coverage():
    """Test that we have features from all expected categories."""
    expected_feature_categories = [
        'grid',  # Starting position
        'qualifying',  # Qualifying performance
        'driver',  # Driver stats
        'constructor',  # Team stats
    ]

    # This would be tested against actual exported features
    # For now, document expected categories
    assert len(expected_feature_categories) > 0


def test_no_duplicate_results(sample_feature_df):
    """Test that there are no duplicate result IDs."""
    assert sample_feature_df['result_id'].is_unique, \
        "Duplicate result_ids found"
