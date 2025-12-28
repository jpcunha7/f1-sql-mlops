"""Export ML features from DuckDB to pandas DataFrames with temporal splits."""

import argparse
import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from f1sqlmlops.config import config
from f1sqlmlops.logging_utils import setup_logger
from f1sqlmlops.warehouse.duckdb_utils import get_connection

logger = setup_logger(__name__)


def export_features(
    db_path: Path = None,
    output_dir: Path = None
) -> Dict[str, pd.DataFrame]:
    """
    Export features from DuckDB with temporal train/val/test splits.

    Args:
        db_path: Path to DuckDB database
        output_dir: Directory to save feature CSVs (optional)

    Returns:
        Dictionary with 'train', 'val', 'test' DataFrames
    """
    db_path = db_path or config.DUCKDB_PATH
    conn = get_connection(db_path)

    logger.info("Exporting features from fct_features_pre_race")

    # Load all features
    query = """
    SELECT * FROM main_marts.fct_features_pre_race
    ORDER BY year, round, result_id
    """

    try:
        df = conn.execute(query).df()
        logger.info(f"Loaded {len(df):,} feature rows")

        # Apply temporal splits
        train_mask = df['year'] <= config.TRAIN_END_YEAR
        val_mask = df['year'].isin(config.VAL_YEARS)
        test_mask = df['year'].isin(config.TEST_YEARS)

        splits = {
            'train': df[train_mask].copy(),
            'val': df[val_mask].copy(),
            'test': df[test_mask].copy()
        }

        for split_name, split_df in splits.items():
            logger.info(
                f"{split_name.upper()}: {len(split_df):,} rows "
                f"(years: {split_df['year'].min()}-{split_df['year'].max()})"
            )

        # Optionally save to CSV
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            for split_name, split_df in splits.items():
                output_path = output_dir / f"features_{split_name}.csv"
                split_df.to_csv(output_path, index=False)
                logger.info(f"Saved {split_name} to {output_path}")

        conn.close()
        return splits

    except Exception as e:
        logger.error(f"Failed to export features: {e}")
        conn.close()
        raise


def get_feature_columns(df: pd.DataFrame) -> Tuple[list, list]:
    """
    Get feature columns and target columns from DataFrame.

    Args:
        df: Features DataFrame

    Returns:
        Tuple of (feature_columns, target_columns)
    """
    # Exclude metadata and target columns from features
    exclude_cols = {
        'result_id',
        'race_id',
        'driver_id',
        'constructor_id',
        'circuit_id',
        'year',
        'round',
        'race_date',
        'target_top_10',
        'target_dnf'
    }

    feature_cols = [col for col in df.columns if col not in exclude_cols]
    target_cols = ['target_top_10', 'target_dnf']

    return feature_cols, target_cols


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Export ML features from DuckDB"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=config.DUCKDB_PATH,
        help="Path to DuckDB database"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save feature CSVs"
    )

    args = parser.parse_args()

    try:
        splits = export_features(args.db_path, args.output_dir)

        # Show feature info
        feature_cols, target_cols = get_feature_columns(splits['train'])
        logger.info(f"Features: {len(feature_cols)} columns")
        logger.info(f"Targets: {target_cols}")

        # Show class distribution
        for target in target_cols:
            logger.info(f"\n{target} distribution:")
            for split_name, split_df in splits.items():
                dist = split_df[target].value_counts()
                pct = split_df[target].mean() * 100
                logger.info(
                    f"  {split_name}: {dist.get(True, 0)} positive "
                    f"({pct:.1f}%), {dist.get(False, 0)} negative"
                )

        sys.exit(0)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
