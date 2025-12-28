"""Download Formula 1 dataset from Kaggle using the Kaggle API."""

import argparse
import sys
from pathlib import Path

from f1sqlmlops.config import config
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


def download_kaggle_dataset(force: bool = False) -> None:
    """
    Download F1 dataset from Kaggle.

    Args:
        force: If True, re-download even if files exist

    Raises:
        ValueError: If Kaggle credentials are not configured
        RuntimeError: If download fails
    """
    # Validate Kaggle credentials
    if not config.KAGGLE_USERNAME or not config.KAGGLE_KEY:
        raise ValueError(
            "Kaggle credentials not found. "
            "Please set KAGGLE_USERNAME and KAGGLE_KEY in .env file. "
            "Get credentials from: https://www.kaggle.com/settings/account"
        )

    # Ensure raw directory exists
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Check if dataset already downloaded
    expected_files = [
        "races.csv",
        "results.csv",
        "drivers.csv",
        "constructors.csv",
        "circuits.csv",
        "qualifying.csv",
        "status.csv",
        "seasons.csv",
    ]

    if not force:
        existing_files = [
            f for f in expected_files if (config.RAW_DIR / f).exists()
        ]
        if len(existing_files) >= len(expected_files) - 2:  # Allow some missing
            logger.info(
                f"Dataset already downloaded ({len(existing_files)}/{len(expected_files)} files found)"
            )
            logger.info("Use --force to re-download")
            return

    logger.info(f"Downloading dataset: {config.KAGGLE_DATASET}")
    logger.info(f"Destination: {config.RAW_DIR}")

    try:
        # Import kaggle here to provide better error message if not installed
        from kaggle.api.kaggle_api_extended import KaggleApi

        # Initialize Kaggle API
        api = KaggleApi()
        api.authenticate()

        # Download and extract dataset
        api.dataset_download_files(
            config.KAGGLE_DATASET,
            path=str(config.RAW_DIR),
            unzip=True,
            quiet=False,
        )

        logger.info("Download completed successfully")

        # Verify downloaded files
        downloaded = list(config.RAW_DIR.glob("*.csv"))
        logger.info(f"Downloaded {len(downloaded)} CSV files")

        for csv_file in sorted(downloaded)[:10]:  # Show first 10
            size_mb = csv_file.stat().st_size / (1024 * 1024)
            logger.info(f"  - {csv_file.name} ({size_mb:.2f} MB)")

        if len(downloaded) > 10:
            logger.info(f"  ... and {len(downloaded) - 10} more files")

    except ImportError:
        raise RuntimeError(
            "Kaggle API not installed. Run: pip install kaggle"
        )
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise RuntimeError(f"Failed to download dataset: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download Formula 1 dataset from Kaggle"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if files exist",
    )

    args = parser.parse_args()

    try:
        download_kaggle_dataset(force=args.force)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
