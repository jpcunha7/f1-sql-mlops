"""Configuration management using environment variables."""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Project configuration loaded from environment variables."""

    # Kaggle API
    KAGGLE_USERNAME: str = os.getenv("KAGGLE_USERNAME", "")
    KAGGLE_KEY: str = os.getenv("KAGGLE_KEY", "")

    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = PROJECT_ROOT / os.getenv("DATA_DIR", "data")
    RAW_DIR: Path = PROJECT_ROOT / os.getenv("RAW_DIR", "data/raw")
    PARQUET_DIR: Path = PROJECT_ROOT / os.getenv("PARQUET_DIR", "data/raw_parquet")
    DUCKDB_PATH: Path = PROJECT_ROOT / os.getenv(
        "DUCKDB_PATH", "data/warehouse/warehouse.duckdb"
    )
    DBT_DIR: Path = PROJECT_ROOT / os.getenv("DBT_DIR", "dbt")
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "./mlruns")
    REPORTS_DIR: Path = PROJECT_ROOT / os.getenv("REPORTS_DIR", "reports")
    MODELS_DIR: Path = PROJECT_ROOT / os.getenv("MODELS_DIR", "models")

    # Random seed
    RANDOM_SEED: int = int(os.getenv("RANDOM_SEED", "42"))

    # Train/val/test split
    TRAIN_END_YEAR: int = int(os.getenv("TRAIN_END_YEAR", "2016"))
    VAL_YEARS: List[int] = [
        int(y.strip()) for y in os.getenv("VAL_YEARS", "2017,2018").split(",")
    ]
    TEST_YEARS: List[int] = [
        int(y.strip()) for y in os.getenv("TEST_YEARS", "2019,2020").split(",")
    ]

    # Kaggle dataset
    KAGGLE_DATASET: str = "rohanrao/formula-1-world-championship-1950-2020"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        for dir_path in [
            cls.DATA_DIR,
            cls.RAW_DIR,
            cls.PARQUET_DIR,
            cls.DUCKDB_PATH.parent,
            cls.REPORTS_DIR,
            cls.MODELS_DIR,
            cls.MODELS_DIR / "top10",
            cls.MODELS_DIR / "dnf",
            Path("predictions"),
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)


config = Config()
