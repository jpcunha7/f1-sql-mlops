"""Tests for configuration."""

import os
from pathlib import Path

import pytest

from f1sqlmlops.config import config


def test_config_paths_are_paths():
    """Test that config paths are Path objects."""
    assert isinstance(config.DATA_DIR, Path)
    assert isinstance(config.PARQUET_DIR, Path)
    assert isinstance(config.DUCKDB_PATH, Path)


def test_config_years_are_integers():
    """Test that year configurations are integers."""
    assert isinstance(config.TRAIN_END_YEAR, int)
    assert isinstance(config.VAL_YEARS, list)
    assert all(isinstance(y, int) for y in config.VAL_YEARS)
    assert isinstance(config.TEST_YEARS, list)
    assert all(isinstance(y, int) for y in config.TEST_YEARS)


def test_temporal_split_logic():
    """Test that temporal splits are logical."""
    # Training ends before validation
    assert config.TRAIN_END_YEAR < min(config.VAL_YEARS)

    # Validation ends before or at test
    assert max(config.VAL_YEARS) <= min(config.TEST_YEARS)

    # No overlap between splits
    val_years_set = set(config.VAL_YEARS)
    test_years_set = set(config.TEST_YEARS)
    assert len(val_years_set & test_years_set) == 0  # No overlap


def test_config_defaults():
    """Test that config has sensible defaults."""
    # Paths should be relative to project root
    assert config.PROJECT_ROOT.exists()

    # Years should be in F1 dataset range
    assert 1950 <= config.TRAIN_END_YEAR <= 2020
    assert all(1950 <= y <= 2020 for y in config.VAL_YEARS)
    assert all(1950 <= y <= 2020 for y in config.TEST_YEARS)


def test_config_kaggle_dataset():
    """Test Kaggle dataset configuration."""
    assert hasattr(config, 'KAGGLE_DATASET')
    assert isinstance(config.KAGGLE_DATASET, str)
    assert '/' in config.KAGGLE_DATASET  # Should be in format "owner/dataset"


def test_config_env_override(monkeypatch, tmp_path):
    """Test that environment variables override defaults."""
    # Set environment variable
    test_path = str(tmp_path / "test_data")
    monkeypatch.setenv("DATA_DIR", test_path)

    # Reimport config to pick up env var
    from importlib import reload

    import f1sqlmlops.config
    reload(f1sqlmlops.config)
    from f1sqlmlops.config import config as reloaded_config

    # Should use env var value
    assert str(reloaded_config.DATA_DIR) == test_path


def test_config_models_dir():
    """Test models directory configuration."""
    assert hasattr(config, 'MODELS_DIR')
    assert isinstance(config.MODELS_DIR, Path)


def test_config_reproducibility():
    """Test that config values are deterministic."""
    # Import config twice and check values are same
    from f1sqlmlops.config import config as config1
    from f1sqlmlops.config import config as config2

    assert config1.TRAIN_END_YEAR == config2.TRAIN_END_YEAR
    assert config1.VAL_YEARS == config2.VAL_YEARS
    assert config1.TEST_YEARS == config2.TEST_YEARS
