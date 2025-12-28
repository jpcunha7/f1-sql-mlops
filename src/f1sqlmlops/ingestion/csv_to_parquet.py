"""Convert CSV files to Parquet format for efficient querying."""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from f1sqlmlops.config import config
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


# Type casting hints for common F1 dataset columns
TYPE_HINTS: Dict[str, Dict[str, str]] = {
    "races": {
        "raceId": "int32",
        "year": "int32",
        "round": "int32",
        "circuitId": "int32",
    },
    "results": {
        "resultId": "int32",
        "raceId": "int32",
        "driverId": "int32",
        "constructorId": "int32",
        "number": "float32",  # Can be missing
        "grid": "int32",
        "position": "float32",  # Can be missing (DNF)
        "positionOrder": "int32",
        "points": "float32",
        "laps": "int32",
        "milliseconds": "float64",  # Can be missing
        "fastestLap": "float32",
        "rank": "float32",
        "statusId": "int32",
    },
    "qualifying": {
        "qualifyId": "int32",
        "raceId": "int32",
        "driverId": "int32",
        "constructorId": "int32",
        "number": "int32",
        "position": "float32",
    },
    "drivers": {
        "driverId": "int32",
        "number": "float32",
    },
    "constructors": {
        "constructorId": "int32",
    },
    "circuits": {
        "circuitId": "int32",
        "lat": "float32",
        "lng": "float32",
        "alt": "float32",
    },
    "status": {
        "statusId": "int32",
    },
}


def convert_csv_to_parquet(
    csv_path: Path,
    parquet_dir: Path,
    table_name: Optional[str] = None,
) -> None:
    """
    Convert a single CSV file to Parquet format.

    Args:
        csv_path: Path to CSV file
        parquet_dir: Directory to save Parquet file
        table_name: Optional table name (defaults to CSV filename)
    """
    if table_name is None:
        table_name = csv_path.stem.lower()

    logger.info(f"Converting {csv_path.name} -> {table_name}.parquet")

    # Read CSV
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        logger.error(f"Failed to read {csv_path.name}: {e}")
        raise

    # Apply type hints if available
    if table_name in TYPE_HINTS:
        type_map = TYPE_HINTS[table_name]
        for col, dtype in type_map.items():
            if col in df.columns:
                try:
                    df[col] = df[col].astype(dtype)
                except Exception as e:
                    logger.warning(
                        f"Could not cast {col} to {dtype} in {table_name}: {e}"
                    )

    # Convert to PyArrow table for better type handling
    try:
        table = pa.Table.from_pandas(df)
    except Exception as e:
        logger.error(f"Failed to convert {table_name} to Arrow table: {e}")
        raise

    # Create output path
    output_path = parquet_dir / f"{table_name}.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write Parquet file
    try:
        pq.write_table(
            table,
            output_path,
            compression="snappy",
            use_dictionary=True,
        )
    except Exception as e:
        logger.error(f"Failed to write Parquet file for {table_name}: {e}")
        raise

    # Log statistics
    original_size = csv_path.stat().st_size / (1024 * 1024)
    parquet_size = output_path.stat().st_size / (1024 * 1024)
    compression_ratio = (
        (1 - parquet_size / original_size) * 100 if original_size > 0 else 0
    )

    logger.info(
        f"  Rows: {len(df):,} | "
        f"Columns: {len(df.columns)} | "
        f"CSV: {original_size:.2f} MB | "
        f"Parquet: {parquet_size:.2f} MB | "
        f"Compression: {compression_ratio:.1f}%"
    )


def convert_all_csv_files(
    raw_dir: Optional[Path] = None,
    parquet_dir: Optional[Path] = None,
) -> None:
    """
    Convert all CSV files in raw directory to Parquet.

    Args:
        raw_dir: Directory containing CSV files (defaults to config)
        parquet_dir: Directory to save Parquet files (defaults to config)
    """
    raw_dir = raw_dir or config.RAW_DIR
    parquet_dir = parquet_dir or config.PARQUET_DIR

    # Find all CSV files
    csv_files = sorted(raw_dir.glob("*.csv"))

    if not csv_files:
        logger.warning(f"No CSV files found in {raw_dir}")
        logger.info("Run 'make ingest' to download data first")
        return

    logger.info(f"Found {len(csv_files)} CSV files to convert")
    logger.info(f"Source: {raw_dir}")
    logger.info(f"Destination: {parquet_dir}")

    parquet_dir.mkdir(parents=True, exist_ok=True)

    # Convert each file
    success_count = 0
    for csv_file in csv_files:
        try:
            convert_csv_to_parquet(csv_file, parquet_dir)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to convert {csv_file.name}: {e}")

    logger.info(
        f"Conversion complete: {success_count}/{len(csv_files)} files successful"
    )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert F1 CSV files to Parquet format"
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=config.RAW_DIR,
        help="Directory containing CSV files",
    )
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=config.PARQUET_DIR,
        help="Directory to save Parquet files",
    )

    args = parser.parse_args()

    try:
        convert_all_csv_files(args.raw_dir, args.parquet_dir)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
