"""Shared pytest fixtures and configuration."""

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture(scope="session")
def project_root():
    """Return project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_races_df():
    """Create a sample races DataFrame."""
    return pd.DataFrame({
        'raceId': [1, 2, 3],
        'year': [2020, 2020, 2021],
        'round': [1, 2, 1],
        'circuitId': [1, 2, 1],
        'name': ['Bahrain GP', 'Saudi GP', 'Bahrain GP'],
        'date': ['2020-11-29', '2020-12-06', '2021-03-28']
    })


@pytest.fixture
def sample_results_df():
    """Create a sample results DataFrame."""
    return pd.DataFrame({
        'resultId': [1, 2, 3, 4, 5, 6],
        'raceId': [1, 1, 1, 2, 2, 2],
        'driverId': [1, 2, 3, 1, 2, 3],
        'constructorId': [1, 2, 1, 1, 2, 1],
        'grid': [1, 2, 3, 1, 2, 3],
        'position': [1, 2, 3, 1, 15, 3],
        'points': [25.0, 18.0, 15.0, 25.0, 0.0, 15.0],
        'laps': [57, 57, 57, 55, 30, 55],
        'statusId': [1, 1, 1, 1, 4, 1]
    })


@pytest.fixture
def sample_drivers_df():
    """Create a sample drivers DataFrame."""
    return pd.DataFrame({
        'driverId': [1, 2, 3],
        'driverRef': ['hamilton', 'verstappen', 'leclerc'],
        'forename': ['Lewis', 'Max', 'Charles'],
        'surname': ['Hamilton', 'Verstappen', 'Leclerc'],
        'nationality': ['British', 'Dutch', 'Monegasque']
    })


@pytest.fixture
def sample_constructors_df():
    """Create a sample constructors DataFrame."""
    return pd.DataFrame({
        'constructorId': [1, 2],
        'constructorRef': ['mercedes', 'red_bull'],
        'name': ['Mercedes', 'Red Bull'],
        'nationality': ['German', 'Austrian']
    })
