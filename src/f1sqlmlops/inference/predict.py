"""Make predictions on new F1 race data."""

import argparse
import pickle
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from f1sqlmlops.config import config
from f1sqlmlops.features.export_features import export_features, get_feature_columns
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


def load_models(models_dir: Path = None) -> Dict[str, object]:
    """
    Load trained models from disk.

    Args:
        models_dir: Directory containing trained models

    Returns:
        Dictionary mapping model names to loaded models
    """
    models_dir = models_dir or config.MODELS_DIR
    models_dir = Path(models_dir)

    models = {}

    # Load top-10 model
    top10_path = models_dir / "top10_classifier.pkl"
    if top10_path.exists():
        logger.info(f"Loading top-10 model from {top10_path}")
        with open(top10_path, 'rb') as f:
            models['top10'] = pickle.load(f)
    else:
        logger.warning(f"Top-10 model not found at {top10_path}")

    # Load DNF model
    dnf_path = models_dir / "dnf_classifier.pkl"
    if dnf_path.exists():
        logger.info(f"Loading DNF model from {dnf_path}")
        with open(dnf_path, 'rb') as f:
            models['dnf'] = pickle.load(f)
    else:
        logger.warning(f"DNF model not found at {dnf_path}")

    if not models:
        raise FileNotFoundError("No trained models found")

    return models


def predict_race(
    features: pd.DataFrame,
    models: Dict[str, object],
    feature_cols: list
) -> pd.DataFrame:
    """
    Make predictions for race results.

    Args:
        features: DataFrame with race features
        models: Dictionary of trained models
        feature_cols: List of feature column names

    Returns:
        DataFrame with predictions added
    """
    X = features[feature_cols]
    predictions = features.copy()

    # Top-10 predictions
    if 'top10' in models:
        top10_proba = models['top10'].predict_proba(X)
        # Handle single-class case
        if top10_proba.shape[1] == 1:
            predictions['top10_probability'] = top10_proba[:, 0]
        else:
            predictions['top10_probability'] = top10_proba[:, 1]
        predictions['top10_prediction'] = models['top10'].predict(X)
    else:
        logger.warning("Top-10 model not available, skipping predictions")

    # DNF predictions
    if 'dnf' in models:
        dnf_proba = models['dnf'].predict_proba(X)
        # Handle single-class case
        if dnf_proba.shape[1] == 1:
            predictions['dnf_probability'] = dnf_proba[:, 0]
        else:
            predictions['dnf_probability'] = dnf_proba[:, 1]
        predictions['dnf_prediction'] = models['dnf'].predict(X)
    else:
        logger.warning("DNF model not available, skipping predictions")

    return predictions


def predict_from_db(
    db_path: Path = None,
    models_dir: Path = None,
    year: Optional[int] = None,
    race_id: Optional[int] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Make predictions on data from DuckDB.

    Args:
        db_path: Path to DuckDB database
        models_dir: Directory containing trained models
        year: Optional year filter
        race_id: Optional race ID filter
        output_path: Optional path to save predictions CSV

    Returns:
        DataFrame with predictions
    """
    logger.info("Loading data from DuckDB")
    splits = export_features(db_path)

    # Combine all splits or filter
    all_data = pd.concat([splits['train'], splits['val'], splits['test']], ignore_index=True)

    # Apply filters
    if year is not None:
        all_data = all_data[all_data['year'] == year]
        logger.info(f"Filtered to year {year}: {len(all_data)} rows")

    if race_id is not None:
        all_data = all_data[all_data['race_id'] == race_id]
        logger.info(f"Filtered to race_id {race_id}: {len(all_data)} rows")

    if len(all_data) == 0:
        logger.error("No data found matching filters")
        return pd.DataFrame()

    # Load models and make predictions
    models = load_models(models_dir)
    feature_cols, _ = get_feature_columns(all_data)

    logger.info(f"Making predictions on {len(all_data)} samples")
    predictions = predict_race(all_data, models, feature_cols)

    # Select relevant columns for output
    output_cols = [
        'race_id', 'year', 'round', 'driver_id',
        'grid_position', 'qualifying_position',
        'top10_probability', 'top10_prediction',
        'dnf_probability', 'dnf_prediction',
        'target_top_10', 'target_dnf'  # Include actuals if available
    ]
    output_cols = [col for col in output_cols if col in predictions.columns]
    result = predictions[output_cols]

    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output_path, index=False)
        logger.info(f"Predictions saved to {output_path}")

    return result


def predict_from_csv(
    csv_path: Path,
    models_dir: Path = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Make predictions on features from CSV file.

    Args:
        csv_path: Path to CSV with features
        models_dir: Directory containing trained models
        output_path: Optional path to save predictions CSV

    Returns:
        DataFrame with predictions
    """
    logger.info(f"Loading features from {csv_path}")
    features = pd.read_csv(csv_path)

    logger.info(f"Loaded {len(features)} samples")

    # Load models and make predictions
    models = load_models(models_dir)
    feature_cols, _ = get_feature_columns(features)

    logger.info(f"Making predictions on {len(features)} samples")
    predictions = predict_race(features, models, feature_cols)

    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        predictions.to_csv(output_path, index=False)
        logger.info(f"Predictions saved to {output_path}")

    return predictions


def format_predictions_summary(predictions: pd.DataFrame) -> str:
    """
    Format predictions as a human-readable summary.

    Args:
        predictions: DataFrame with predictions

    Returns:
        Formatted summary string
    """
    summary = []
    summary.append(f"\n{'='*80}")
    summary.append("RACE PREDICTIONS SUMMARY")
    summary.append(f"{'='*80}\n")

    # Group by race
    for race_id in predictions['race_id'].unique():
        race_data = predictions[predictions['race_id'] == race_id].copy()
        year = race_data['year'].iloc[0]
        round_num = race_data['round'].iloc[0]

        summary.append(f"\n{year} - Round {round_num} (Race ID: {race_id})")
        summary.append("-" * 80)

        # Sort by top-10 probability descending
        race_data = race_data.sort_values('top10_probability', ascending=False)

        # Show top predictions
        summary.append(f"{'Driver ID':>10} {'Grid':>6} {'Top-10 Prob':>12} {'DNF Prob':>10} {'Prediction':>15}")
        summary.append("-" * 80)

        for _, row in race_data.head(10).iterrows():
            driver_id = int(row['driver_id'])
            grid = int(row['grid_position']) if pd.notna(row['grid_position']) else 0
            top10_prob = row['top10_probability']
            dnf_prob = row['dnf_probability']

            if row['top10_prediction']:
                prediction = "TOP-10"
            elif row['dnf_prediction']:
                prediction = "DNF"
            else:
                prediction = "11th-20th"

            summary.append(
                f"{driver_id:10d} {grid:6d} {top10_prob:12.1%} {dnf_prob:10.1%} {prediction:>15}"
            )

        # Statistics
        summary.append("")
        summary.append(f"Total drivers: {len(race_data)}")
        summary.append(f"Predicted top-10 finishers: {race_data['top10_prediction'].sum()}")
        summary.append(f"Predicted DNFs: {race_data['dnf_prediction'].sum()}")
        summary.append(f"Average top-10 probability: {race_data['top10_probability'].mean():.1%}")
        summary.append(f"Average DNF probability: {race_data['dnf_probability'].mean():.1%}")

        # Show accuracy if actuals are available
        if 'target_top_10' in race_data.columns:
            top10_acc = (race_data['top10_prediction'] == race_data['target_top_10']).mean()
            summary.append(f"Top-10 prediction accuracy: {top10_acc:.1%}")

        if 'target_dnf' in race_data.columns:
            dnf_acc = (race_data['dnf_prediction'] == race_data['target_dnf']).mean()
            summary.append(f"DNF prediction accuracy: {dnf_acc:.1%}")

    return "\n".join(summary)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Make predictions on F1 race data"
    )

    # Input source
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--from-db",
        action="store_true",
        help="Load data from DuckDB"
    )
    input_group.add_argument(
        "--from-csv",
        type=Path,
        help="Load features from CSV file"
    )

    # Filters (for DB mode)
    parser.add_argument(
        "--year",
        type=int,
        help="Filter to specific year (DB mode only)"
    )
    parser.add_argument(
        "--race-id",
        type=int,
        help="Filter to specific race ID (DB mode only)"
    )

    # Paths
    parser.add_argument(
        "--db-path",
        type=Path,
        default=config.DUCKDB_PATH,
        help="Path to DuckDB database"
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=config.MODELS_DIR,
        help="Directory containing trained models"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to save predictions CSV"
    )

    # Output format
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print human-readable summary"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output predictions as JSON"
    )

    args = parser.parse_args()

    try:
        # Make predictions
        if args.from_db:
            predictions = predict_from_db(
                db_path=args.db_path,
                models_dir=args.models_dir,
                year=args.year,
                race_id=args.race_id,
                output_path=args.output
            )
        else:
            predictions = predict_from_csv(
                csv_path=args.from_csv,
                models_dir=args.models_dir,
                output_path=args.output
            )

        if len(predictions) == 0:
            logger.error("No predictions generated")
            sys.exit(1)

        # Output results
        if args.summary:
            print(format_predictions_summary(predictions))
        elif args.json:
            print(predictions.to_json(orient='records', indent=2))
        else:
            # Default: show first few rows
            logger.info(f"\nPredictions generated for {len(predictions)} samples")
            logger.info("\nFirst 10 predictions:")
            print(predictions.head(10).to_string(index=False))

        logger.info(f"\n✓ Successfully generated {len(predictions)} predictions")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
