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

    assert len(races) == 6  # 2 seasons * 3 races
    assert all(isinstance(r, dict) for r in races)
    assert all('raceId' in r for r in races)
    assert all('year' in r for r in races)
    assert all('round' in r for r in races)
    assert races[0]['year'] == 2020
    assert races[3]['year'] == 2021


def test_generate_toy_circuits():
    """Test that toy circuits are generated with required fields."""
    circuits = generate_toy_circuits(n_circuits=5)

    assert len(circuits) == 5
    assert all('circuitId' in c for c in circuits)
    assert all('circuitRef' in c for c in circuits)
    assert all('name' in c for c in circuits)
    assert all('country' in c for c in circuits)


def test_generate_toy_drivers():
    """Test that toy drivers are generated with required fields."""
    drivers = generate_toy_drivers(n_drivers=10)

    assert len(drivers) == 10
    assert all('driverId' in d for d in drivers)
    assert all('driverRef' in d for d in drivers)
    assert all('forename' in d for d in drivers)
    assert all('surname' in d for d in drivers)
    assert all('nationality' in d for d in drivers)


def test_generate_toy_constructors():
    """Test that toy constructors are generated with required fields."""
    constructors = generate_toy_constructors(n_constructors=5)

    assert len(constructors) == 5
    assert all('constructorId' in c for c in constructors)
    assert all('constructorRef' in c for c in constructors)
    assert all('name' in c for c in constructors)
    assert all('nationality' in c for c in constructors)


def test_generate_toy_qualifying():
    """Test qualifying data generation."""
    races = generate_toy_races(n_seasons=1, races_per_season=2)
    qualifying = generate_toy_qualifying(races, drivers_per_race=10)

    # Should have entries for all races
    assert len(qualifying) >= 20  # 2 races * 10 drivers
    assert all('qualifyId' in q for q in qualifying)
    assert all('raceId' in q for q in qualifying)
    assert all('driverId' in q for q in qualifying)
    assert all('position' in q for q in qualifying)


def test_generate_toy_results():
    """Test results data generation."""
    races = generate_toy_races(n_seasons=1, races_per_season=2)
    results = generate_toy_results(races, drivers_per_race=10)

    # Should have entries for all races
    assert len(results) >= 20  # 2 races * 10 drivers
    assert all('resultId' in r for r in results)
    assert all('raceId' in r for r in results)
    assert all('driverId' in r for r in results)
    assert all('constructorId' in r for r in results)
    assert all('grid' in r for r in results)
    assert all('position' in r for r in results)

    # Check that DNF status is set for some drivers
    dnf_statuses = [r['statusId'] for r in results if r['statusId'] != 1]
    assert len(dnf_statuses) > 0  # At least some DNFs


def test_generate_toy_dataset(tmp_path):
    """Test full dataset generation with file output."""
    output_dir = tmp_path / "toy_data"

    generate_toy_dataset(
        output_dir=output_dir,
        n_seasons=2,
        races_per_season=2,
        drivers_per_race=5
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
        'constructor_results.parquet'
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

    years = {r['year'] for r in races}

    # Should have training data (≤2016)
    assert any(y <= 2016 for y in years)

    # Should have validation data (2017-2018)
    assert 2017 in years or 2018 in years

    # Should have test data (2019-2020)
    assert 2019 in years or 2020 in years


def test_toy_data_consistency():
    """Test that relationships between tables are consistent."""
    races = generate_toy_races(n_seasons=2, races_per_season=3)
    results = generate_toy_results(races, drivers_per_race=10)
    qualifying = generate_toy_qualifying(races, drivers_per_race=10)

    # All result race IDs should exist in races
    race_ids = {r['raceId'] for r in races}
    result_race_ids = {r['raceId'] for r in results}
    assert result_race_ids.issubset(race_ids)

    # All qualifying race IDs should exist in races
    quali_race_ids = {q['raceId'] for q in qualifying}
    assert quali_race_ids.issubset(race_ids)

    # Driver IDs should be consistent between qualifying and results
    result_driver_ids = {r['driverId'] for r in results}
    quali_driver_ids = {q['driverId'] for q in qualifying}
    # There should be overlap (drivers in both qualifying and results)
    assert len(result_driver_ids & quali_driver_ids) > 0
