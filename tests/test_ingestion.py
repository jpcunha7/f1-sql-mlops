"""Tests for data ingestion modules."""

import pytest
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

from f1sqlmlops.ingestion.generate_toy_data import (
    generate_toy_races,
    generate_toy_drivers,
    generate_toy_constructors,
    generate_toy_dataset,
)
from f1sqlmlops.quality.schema_checks import validate_parquet_schema


def test_generate_toy_races():
    """Test synthetic races generation."""
    df = generate_toy_races(n_seasons=2, races_per_season=3)
    assert len(df) == 6  # 2 seasons * 3 races
    assert "raceId" in df.columns
    assert "year" in df.columns
    assert df["raceId"].is_unique


def test_generate_toy_drivers():
    """Test synthetic drivers generation."""
    df = generate_toy_drivers(n_drivers=5)
    assert len(df) == 5
    assert "driverId" in df.columns
    assert "code" in df.columns
    assert df["driverId"].is_unique


def test_generate_toy_constructors():
    """Test synthetic constructors generation."""
    df = generate_toy_constructors(n_teams=3)
    assert len(df) == 3
    assert "constructorId" in df.columns
    assert "name" in df.columns


def test_generate_full_toy_dataset(tmp_path):
    """Test complete toy dataset generation."""
    output_dir = tmp_path / "toy_data"
    generate_toy_dataset(output_dir)

    # Check that files were created
    expected_files = [
        "races.parquet",
        "drivers.parquet",
        "constructors.parquet",
        "circuits.parquet",
        "status.parquet",
        "qualifying.parquet",
        "results.parquet",
        "seasons.parquet",
    ]

    for filename in expected_files:
        filepath = output_dir / filename
        assert filepath.exists(), f"{filename} not created"

        # Verify it's valid Parquet
        df = pd.read_parquet(filepath)
        assert len(df) > 0, f"{filename} is empty"


def test_schema_validation(tmp_path):
    """Test schema validation with toy data."""
    # Generate toy dataset
    output_dir = tmp_path / "toy_data"
    generate_toy_dataset(output_dir)

    # Validate races schema
    races_path = output_dir / "races.parquet"
    required_cols = {"raceId", "year", "round", "circuitId", "name", "date"}

    is_valid, missing = validate_parquet_schema(races_path, required_cols)
    assert is_valid, f"Schema validation failed: missing {missing}"
    assert len(missing) == 0
