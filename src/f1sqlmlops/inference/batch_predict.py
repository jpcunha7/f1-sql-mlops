"""Batch prediction script for multiple races."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

from f1sqlmlops.config import config
from f1sqlmlops.inference.predict import (
    format_predictions_summary,
    load_models,
    predict_race,
)
from f1sqlmlops.features.export_features import export_features, get_feature_columns
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


def batch_predict(
    db_path: Path = None,
    models_dir: Path = None,
    years: Optional[List[int]] = None,
    output_dir: Path = None
) -> pd.DataFrame:
    """
    Generate predictions for multiple races.

    Args:
        db_path: Path to DuckDB database
        models_dir: Directory containing trained models
        years: List of years to predict (if None, uses test years)
        output_dir: Directory to save prediction files

    Returns:
        DataFrame with all predictions
    """
    # Load data
    logger.info("Loading data from DuckDB")
    splits = export_features(db_path)

    # Use test split by default, or filter by years
    if years is None:
        data = splits['test']
        logger.info(f"Using test split: {len(data)} samples")
    else:
        all_data = pd.concat([splits['train'], splits['val'], splits['test']], ignore_index=True)
        data = all_data[all_data['year'].isin(years)]
        logger.info(f"Filtered to years {years}: {len(data)} samples")

    if len(data) == 0:
        logger.error("No data found")
        return pd.DataFrame()

    # Load models
    models = load_models(models_dir)
    feature_cols, _ = get_feature_columns(data)

    # Make predictions
    logger.info(f"Making predictions on {len(data)} samples")
    predictions = predict_race(data, models, feature_cols)

    # Save outputs
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save all predictions
        all_predictions_path = output_dir / "all_predictions.csv"
        predictions.to_csv(all_predictions_path, index=False)
        logger.info(f"Saved all predictions to {all_predictions_path}")

        # Save per-race predictions
        for race_id in predictions['race_id'].unique():
            race_data = predictions[predictions['race_id'] == race_id]
            year = race_data['year'].iloc[0]
            round_num = race_data['round'].iloc[0]
            race_file = output_dir / f"{year}_round_{round_num}_race_{race_id}.csv"
            race_data.to_csv(race_file, index=False)

        logger.info(f"Saved {len(predictions['race_id'].unique())} race-specific files")

        # Save summary report
        summary_path = output_dir / "predictions_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(format_predictions_summary(predictions))
        logger.info(f"Saved summary report to {summary_path}")

    return predictions


def evaluate_predictions(predictions: pd.DataFrame) -> dict:
    """
    Evaluate prediction accuracy if ground truth is available.

    Args:
        predictions: DataFrame with predictions and actuals

    Returns:
        Dictionary of evaluation metrics
    """
    metrics = {}

    if 'target_top_10' in predictions.columns and 'top10_prediction' in predictions.columns:
        top10_acc = (predictions['top10_prediction'] == predictions['target_top_10']).mean()
        metrics['top10_accuracy'] = top10_acc

        # By year
        top10_by_year = predictions.groupby('year').apply(
            lambda x: (x['top10_prediction'] == x['target_top_10']).mean()
        ).to_dict()
        metrics['top10_accuracy_by_year'] = top10_by_year

    if 'target_dnf' in predictions.columns and 'dnf_prediction' in predictions.columns:
        dnf_acc = (predictions['dnf_prediction'] == predictions['target_dnf']).mean()
        metrics['dnf_accuracy'] = dnf_acc

        # By year
        dnf_by_year = predictions.groupby('year').apply(
            lambda x: (x['dnf_prediction'] == x['target_dnf']).mean()
        ).to_dict()
        metrics['dnf_accuracy_by_year'] = dnf_by_year

    return metrics


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch predict F1 race results"
    )
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
        "--years",
        type=int,
        nargs='+',
        help="Years to predict (default: test years)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.DATA_DIR / "predictions",
        help="Directory to save prediction files"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate predictions against ground truth"
    )

    args = parser.parse_args()

    try:
        # Generate predictions
        predictions = batch_predict(
            db_path=args.db_path,
            models_dir=args.models_dir,
            years=args.years,
            output_dir=args.output_dir
        )

        if len(predictions) == 0:
            logger.error("No predictions generated")
            sys.exit(1)

        logger.info(f"\n✓ Generated predictions for {len(predictions)} samples")
        logger.info(f"  Races: {predictions['race_id'].nunique()}")
        logger.info(f"  Years: {sorted(predictions['year'].unique())}")

        # Evaluate if requested
        if args.evaluate:
            logger.info("\nEvaluating predictions...")
            metrics = evaluate_predictions(predictions)

            if metrics:
                logger.info("\nEVALUATION RESULTS:")
                logger.info("=" * 60)

                if 'top10_accuracy' in metrics:
                    logger.info(f"Top-10 Overall Accuracy: {metrics['top10_accuracy']:.2%}")
                    if 'top10_accuracy_by_year' in metrics:
                        logger.info("  By year:")
                        for year, acc in sorted(metrics['top10_accuracy_by_year'].items()):
                            logger.info(f"    {year}: {acc:.2%}")

                if 'dnf_accuracy' in metrics:
                    logger.info(f"\nDNF Overall Accuracy: {metrics['dnf_accuracy']:.2%}")
                    if 'dnf_accuracy_by_year' in metrics:
                        logger.info("  By year:")
                        for year, acc in sorted(metrics['dnf_accuracy_by_year'].items()):
                            logger.info(f"    {year}: {acc:.2%}")
            else:
                logger.warning("No ground truth available for evaluation")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
