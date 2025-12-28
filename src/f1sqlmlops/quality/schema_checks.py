"""Schema validation for F1 dataset tables."""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

import pyarrow.parquet as pq

from f1sqlmlops.config import config
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


# Expected schema: table_name -> required columns
REQUIRED_SCHEMAS: Dict[str, Set[str]] = {
    "races": {
        "raceId",
        "year",
        "round",
        "circuitId",
        "name",
        "date",
    },
    "results": {
        "resultId",
        "raceId",
        "driverId",
        "constructorId",
        "grid",
        "position",
        "positionOrder",
        "points",
        "laps",
        "statusId",
    },
    "qualifying": {
        "qualifyId",
        "raceId",
        "driverId",
        "constructorId",
        "position",
    },
    "drivers": {
        "driverId",
        "driverRef",
        "code",
        "forename",
        "surname",
        "nationality",
    },
    "constructors": {
        "constructorId",
        "constructorRef",
        "name",
        "nationality",
    },
    "circuits": {
        "circuitId",
        "circuitRef",
        "name",
        "location",
        "country",
    },
    "status": {
        "statusId",
        "status",
    },
}

# Optional tables (won't fail if missing)
OPTIONAL_TABLES = {
    "sprint_results",
    "pit_stops",
    "lap_times",
    "constructor_results",
    "constructor_standings",
    "driver_standings",
    "seasons"
}


def validate_parquet_schema(
    parquet_path: Path, required_columns: Set[str]
) -> tuple[bool, List[str]]:
    """
    Validate that a Parquet file has required columns.

    Args:
        parquet_path: Path to Parquet file
        required_columns: Set of required column names

    Returns:
        Tuple of (is_valid, missing_columns)
    """
    try:
        # Read Parquet schema
        parquet_file = pq.ParquetFile(parquet_path)
        schema = parquet_file.schema

        # Get column names (preserve original case for matching)
        actual_columns_lower = {field.name.lower() for field in schema}
        required_columns_lower = {col.lower() for col in required_columns}

        # Check for missing columns
        missing = required_columns_lower - actual_columns_lower
        # Return original case for error reporting
        missing = sorted(missing)

        return len(missing) == 0, sorted(missing)

    except Exception as e:
        logger.error(f"Failed to read schema from {parquet_path.name}: {e}")
        return False, []


def validate_all_schemas(parquet_dir: Optional[Path] = None) -> bool:
    """
    Validate schemas for all required tables.

    Args:
        parquet_dir: Directory containing Parquet files

    Returns:
        True if all validations pass, False otherwise
    """
    parquet_dir = parquet_dir or config.PARQUET_DIR

    if not parquet_dir.exists():
        logger.error(f"Parquet directory not found: {parquet_dir}")
        logger.info("Run 'make ingest' first to download and convert data")
        return False

    logger.info(f"Validating schemas in: {parquet_dir}")

    all_valid = True
    validated_count = 0

    for table_name, required_cols in REQUIRED_SCHEMAS.items():
        parquet_path = parquet_dir / f"{table_name}.parquet"

        if not parquet_path.exists():
            logger.error(f"Required table missing: {table_name}.parquet")
            all_valid = False
            continue

        is_valid, missing_cols = validate_parquet_schema(
            parquet_path, required_cols
        )

        if is_valid:
            logger.info(f"✓ {table_name}: Valid schema")
            validated_count += 1
        else:
            logger.error(
                f"✗ {table_name}: Missing columns: {', '.join(missing_cols)}"
            )
            all_valid = False

    # Check for optional tables
    for table_name in OPTIONAL_TABLES:
        parquet_path = parquet_dir / f"{table_name}.parquet"
        if parquet_path.exists():
            logger.info(f"  {table_name}: Found (optional)")

    logger.info("")
    logger.info(
        f"Validation complete: {validated_count}/{len(REQUIRED_SCHEMAS)} required tables valid"
    )

    if all_valid:
        logger.info("All schema validations passed")
    else:
        logger.error("Schema validation failed")

    return all_valid


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate F1 dataset schemas"
    )
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=config.PARQUET_DIR,
        help="Directory containing Parquet files",
    )

    args = parser.parse_args()

    try:
        valid = validate_all_schemas(args.parquet_dir)
        sys.exit(0 if valid else 1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
