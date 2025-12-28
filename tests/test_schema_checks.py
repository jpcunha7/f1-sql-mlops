"""Tests for schema validation."""

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from f1sqlmlops.quality.schema_checks import (
    REQUIRED_SCHEMAS,
    validate_all_schemas,
    validate_parquet_schema,
)


@pytest.fixture
def tmp_parquet_dir(tmp_path):
    """Create a temporary directory with valid parquet files."""
    parquet_dir = tmp_path / "parquet"
    parquet_dir.mkdir()

    # Create races parquet with valid schema
    races_df = pd.DataFrame({
        'raceId': [1, 2],
        'year': [2020, 2020],
        'round': [1, 2],
        'circuitId': [1, 2],
        'name': ['Race 1', 'Race 2'],
        'date': ['2020-03-15', '2020-03-22']
    })
    races_df.to_parquet(parquet_dir / 'races.parquet', index=False)

    # Create results parquet with valid schema
    results_df = pd.DataFrame({
        'resultId': [1, 2],
        'raceId': [1, 1],
        'driverId': [1, 2],
        'constructorId': [1, 2],
        'grid': [1, 2],
        'position': [1, 2],
        'points': [25.0, 18.0],
        'laps': [50, 50],
        'statusId': [1, 1]
    })
    results_df.to_parquet(parquet_dir / 'results.parquet', index=False)

    # Create drivers parquet
    drivers_df = pd.DataFrame({
        'driverId': [1, 2],
        'driverRef': ['ham', 'ver'],
        'forename': ['Lewis', 'Max'],
        'surname': ['Hamilton', 'Verstappen'],
        'nationality': ['British', 'Dutch']
    })
    drivers_df.to_parquet(parquet_dir / 'drivers.parquet', index=False)

    return parquet_dir


def test_validate_parquet_schema_valid(tmp_parquet_dir):
    """Test schema validation with valid parquet file."""
    races_path = tmp_parquet_dir / 'races.parquet'
    required_columns = REQUIRED_SCHEMAS['races']

    # Should not raise an exception
    validate_parquet_schema(races_path, required_columns)


def test_validate_parquet_schema_missing_columns(tmp_path):
    """Test schema validation with missing required columns."""
    # Create parquet with missing columns
    df = pd.DataFrame({
        'raceId': [1, 2],
        'year': [2020, 2020]
        # Missing: round, circuitId, name, date
    })
    parquet_path = tmp_path / 'incomplete.parquet'
    df.to_parquet(parquet_path, index=False)

    required_columns = REQUIRED_SCHEMAS['races']

    is_valid, missing_cols = validate_parquet_schema(parquet_path, required_columns)
    assert not is_valid, "Should detect missing columns"
    assert len(missing_cols) > 0, "Should return list of missing columns"


def test_validate_parquet_schema_case_insensitive(tmp_path):
    """Test that schema validation is case-insensitive."""
    # Create parquet with different case columns
    df = pd.DataFrame({
        'raceid': [1, 2],  # lowercase instead of raceId
        'YEAR': [2020, 2020],  # uppercase
        'Round': [1, 2],  # mixed case
        'circuitid': [1, 2],
        'NAME': ['Race 1', 'Race 2'],
        'date': ['2020-03-15', '2020-03-22']
    })
    parquet_path = tmp_path / 'mixed_case.parquet'
    df.to_parquet(parquet_path, index=False)

    required_columns = REQUIRED_SCHEMAS['races']

    # Should not raise an exception (case-insensitive)
    validate_parquet_schema(parquet_path, required_columns)


def test_validate_all_schemas_success(tmp_parquet_dir):
    """Test validation of all schemas with valid files."""
    # Only validate files that exist
    existing_tables = ['races', 'results', 'drivers']

    # Should complete without raising exceptions
    for table_name in existing_tables:
        parquet_path = tmp_parquet_dir / f'{table_name}.parquet'
        if parquet_path.exists():
            required_columns = REQUIRED_SCHEMAS[table_name]
            validate_parquet_schema(parquet_path, required_columns)


def test_validate_all_schemas_with_function(tmp_parquet_dir):
    """Test the validate_all_schemas function."""
    # This should validate all existing files
    # It will skip files that don't exist (like constructors, circuits, etc.)
    # Should not raise an exception
    validate_all_schemas(parquet_dir=tmp_parquet_dir)


def test_required_schemas_completeness():
    """Test that REQUIRED_SCHEMAS contains all expected tables."""
    expected_tables = [
        'races', 'results', 'drivers', 'constructors',
        'circuits', 'qualifying', 'status', 'constructor_results'
    ]

    for table in expected_tables:
        assert table in REQUIRED_SCHEMAS, f"Missing schema definition for {table}"
        assert len(REQUIRED_SCHEMAS[table]) > 0, f"Empty schema for {table}"


def test_schema_has_primary_keys():
    """Test that schemas include expected primary key columns."""
    # Check that each table has its primary key
    assert 'raceId' in REQUIRED_SCHEMAS['races']
    assert 'resultId' in REQUIRED_SCHEMAS['results']
    assert 'driverId' in REQUIRED_SCHEMAS['drivers']
    assert 'constructorId' in REQUIRED_SCHEMAS['constructors']
    assert 'circuitId' in REQUIRED_SCHEMAS['circuits']
    assert 'qualifyId' in REQUIRED_SCHEMAS['qualifying']
    assert 'statusId' in REQUIRED_SCHEMAS['status']


def test_schema_has_foreign_keys():
    """Test that schemas include expected foreign key columns."""
    # Results should reference races, drivers, constructors
    assert 'raceId' in REQUIRED_SCHEMAS['results']
    assert 'driverId' in REQUIRED_SCHEMAS['results']
    assert 'constructorId' in REQUIRED_SCHEMAS['results']

    # Qualifying should reference races and drivers
    assert 'raceId' in REQUIRED_SCHEMAS['qualifying']
    assert 'driverId' in REQUIRED_SCHEMAS['qualifying']

    # Races should reference circuits
    assert 'circuitId' in REQUIRED_SCHEMAS['races']
