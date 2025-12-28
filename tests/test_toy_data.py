"""Tests for toy data generation."""

from pathlib import Path

import pandas as pd
import pytest

from f1sqlmlops.ingestion.generate_toy_data import (
    generate_toy_circuits,
    generate_toy_constructors,
    generate_toy_dataset,
    generate_toy_drivers,
    generate_toy_qualifying,
    generate_toy_races,
    generate_toy_results,
)


def test_generate_toy_races():
    """Test that toy races are generated with correct structure."""
    races = generate_toy_races(n_seasons=2, races_per_season=3, start_year=2020)

    assert isinstance(races, pd.DataFrame)
    assert len(races) == 6  # 2 seasons * 3 races
    assert 'raceId' in races.columns
    assert 'year' in races.columns
    assert 'round' in races.columns
    assert races.iloc[0]['year'] == 2020
    assert races.iloc[3]['year'] == 2021


def test_generate_toy_circuits():
    """Test that toy circuits are generated with required fields."""
    circuits = generate_toy_circuits(n_circuits=5)

    assert isinstance(circuits, pd.DataFrame)
    assert len(circuits) == 5
    assert 'circuitId' in circuits.columns
    assert 'circuitRef' in circuits.columns
    assert 'name' in circuits.columns
    assert 'country' in circuits.columns


def test_generate_toy_drivers():
    """Test that toy drivers are generated with required fields."""
    drivers = generate_toy_drivers(n_drivers=10)

    assert isinstance(drivers, pd.DataFrame)
    assert len(drivers) == 10
    assert 'driverId' in drivers.columns
    assert 'driverRef' in drivers.columns
    assert 'forename' in drivers.columns
    assert 'surname' in drivers.columns
    assert 'nationality' in drivers.columns


def test_generate_toy_constructors():
    """Test that toy constructors are generated with required fields."""
    constructors = generate_toy_constructors(n_teams=5)

    assert isinstance(constructors, pd.DataFrame)
    assert len(constructors) == 5
    assert 'constructorId' in constructors.columns
    assert 'constructorRef' in constructors.columns
    assert 'name' in constructors.columns
    assert 'nationality' in constructors.columns


def test_generate_toy_qualifying():
    """Test qualifying data generation."""
    races = generate_toy_races(n_seasons=1, races_per_season=2)
    drivers = generate_toy_drivers(n_drivers=10)
    qualifying = generate_toy_qualifying(races, drivers)

    assert isinstance(qualifying, pd.DataFrame)
    # Should have entries for all races
    assert len(qualifying) >= 20  # 2 races * 10 drivers
    assert 'qualifyId' in qualifying.columns
    assert 'raceId' in qualifying.columns
    assert 'driverId' in qualifying.columns
    assert 'position' in qualifying.columns


def test_generate_toy_results():
    """Test results data generation."""
    races = generate_toy_races(n_seasons=1, races_per_season=2)
    drivers = generate_toy_drivers(n_drivers=10)
    status = pd.DataFrame([
        {"statusId": 1, "status": "Finished"},
        {"statusId": 3, "status": "Accident"}
    ])
    results = generate_toy_results(races, drivers, status)

    assert isinstance(results, pd.DataFrame)
    # Should have entries for all races
    assert len(results) >= 20  # 2 races * 10 drivers
    assert 'resultId' in results.columns
    assert 'raceId' in results.columns
    assert 'driverId' in results.columns
    assert 'constructorId' in results.columns
    assert 'grid' in results.columns
    assert 'position' in results.columns

    # Check that DNF status is set for some drivers
    dnf_statuses = results[results['statusId'] != 1]
    assert len(dnf_statuses) > 0  # At least some DNFs


def test_generate_toy_dataset(tmp_path):
    """Test full dataset generation with file output."""
    output_dir = tmp_path / "toy_data"

    generate_toy_dataset(
        output_dir=output_dir,
        n_seasons=2,
        races_per_season=2,
        n_drivers=5
    )

    # Check that all expected files were created
    expected_files = [
        'circuits.parquet',
        'drivers.parquet',
        'constructors.parquet',
        'races.parquet',
        'qualifying.parquet',
        'results.parquet',
        'status.parquet',
        'seasons.parquet'
    ]

    for filename in expected_files:
        file_path = output_dir / filename
        assert file_path.exists(), f"Missing file: {filename}"

        # Verify it's a valid parquet file
        df = pd.read_parquet(file_path)
        assert len(df) > 0, f"Empty file: {filename}"


def test_toy_data_temporal_coverage():
    """Test that toy data covers train/val/test splits."""
    # Generate 7 seasons (2014-2020) to cover all splits
    races = generate_toy_races(n_seasons=7, races_per_season=5, start_year=2014)

    years = set(races['year'].unique())

    # Should have training data (≤2016)
    assert any(y <= 2016 for y in years)

    # Should have validation data (2017-2018)
    assert 2017 in years or 2018 in years

    # Should have test data (2019-2020)
    assert 2019 in years or 2020 in years


def test_toy_data_consistency():
    """Test that relationships between tables are consistent."""
    races = generate_toy_races(n_seasons=2, races_per_season=3)
    drivers = generate_toy_drivers(n_drivers=10)
    status = pd.DataFrame([{"statusId": 1, "status": "Finished"}, {"statusId": 3, "status": "Accident"}])
    results = generate_toy_results(races, drivers, status)
    qualifying = generate_toy_qualifying(races, drivers)

    # All result race IDs should exist in races
    race_ids = set(races['raceId'].unique())
    result_race_ids = set(results['raceId'].unique())
    assert result_race_ids.issubset(race_ids)

    # All qualifying race IDs should exist in races
    quali_race_ids = set(qualifying['raceId'].unique())
    assert quali_race_ids.issubset(race_ids)

    # Driver IDs should be consistent between qualifying and results
    result_driver_ids = set(results['driverId'].unique())
    quali_driver_ids = set(qualifying['driverId'].unique())
    # There should be overlap (drivers in both qualifying and results)
    assert len(result_driver_ids & quali_driver_ids) > 0
