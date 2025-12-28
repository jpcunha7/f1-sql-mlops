"""
Generate Evidently reports for model evaluation and data drift analysis.

This module creates HTML reports using the Evidently library to visualize:
- Classification performance for Top-10 and DNF models
- Data drift between training and test sets
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from evidently import Report
from evidently.presets import ClassificationPreset, DataDriftPreset

from f1sqlmlops.config import config
from f1sqlmlops.features.export_features import export_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_classification_report(
    y_true: pd.Series,
    y_pred: pd.Series,
    y_proba: pd.Series,
    model_name: str,
    output_path: Path
) -> None:
    """
    Generate Evidently classification performance report.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_proba: Predicted probabilities (for positive class)
        model_name: Name of the model (for report title)
        output_path: Path to save HTML report
    """
    logger.info(f"Generating classification report for {model_name}...")

    # Create DataFrame with predictions
    df = pd.DataFrame({
        "target": y_true.astype(str),  # Convert to string for Evidently
        "prediction": y_pred.astype(str)
    })

    # Create report with classification metrics
    report = Report(metrics=[
        ClassificationPreset()
    ])

    # Run report
    try:
        report.run(current_data=df)

        # Save HTML report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report.save_html(str(output_path))

        logger.info(f"✓ Classification report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        logger.warning(f"Skipping {model_name} report due to error")


def generate_drift_report(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: list,
    output_path: Path
) -> None:
    """
    Generate Evidently data drift report comparing train and test sets.

    Args:
        train_df: Training data (reference)
        test_df: Test data (current)
        feature_cols: List of feature columns to analyze
        output_path: Path to save HTML report
    """
    logger.info("Generating data drift report...")

    # Select only feature columns for drift analysis
    train_features = train_df[feature_cols].copy()
    test_features = test_df[feature_cols].copy()

    # Create report with drift metrics
    report = Report(metrics=[
        DataDriftPreset()
    ])

    # Run report (train as reference, test as current)
    try:
        report.run(
            reference_data=train_features,
            current_data=test_features
        )

        # Save HTML report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report.save_html(str(output_path))

        logger.info(f"✓ Data drift report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate drift report: {e}")
        logger.warning("Skipping drift report due to error")


def generate_all_reports(
    db_path: Optional[Path] = None,
    models_dir: Optional[Path] = None,
    features_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None
) -> None:
    """
    Generate all Evidently reports for the project.

    This function:
    1. Loads test set predictions from both models
    2. Generates classification reports for Top-10 and DNF models
    3. Generates drift report comparing train vs test features

    Args:
        db_path: Path to DuckDB database
        models_dir: Directory containing trained models
        features_dir: Directory containing exported features
        reports_dir: Directory to save reports
    """
    # Set defaults
    if db_path is None:
        db_path = config.DUCKDB_PATH
    if models_dir is None:
        models_dir = config.MODELS_DIR
    if features_dir is None:
        features_dir = config.DATA_DIR / "features"
    if reports_dir is None:
        reports_dir = config.PROJECT_ROOT / "reports"

    logger.info("=" * 60)
    logger.info("EVIDENTLY REPORT GENERATION")
    logger.info("=" * 60)

    # Load feature splits
    logger.info("Loading feature data...")
    splits = export_features(db_path=db_path, output_dir=features_dir)
    train_df = splits["train"]
    test_df = splits["test"]

    # Identify feature columns (exclude metadata)
    exclude_cols = {
        "race_id", "driver_id", "constructor_id", "circuit_id",
        "year", "round", "result_id", "race_date",
        "is_top_10", "is_dnf", "final_position", "status"
    }
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]

    logger.info(f"Found {len(feature_cols)} feature columns")

    # Load predictions from saved files
    top10_preds_path = reports_dir / "top10_test_predictions.csv"
    dnf_preds_path = reports_dir / "dnf_test_predictions.csv"

    # Generate classification reports
    try:
        if top10_preds_path.exists():
            logger.info("Generating Top-10 classification report...")
            top10_preds = pd.read_csv(top10_preds_path)

            # Handle single-class case
            if "probability" in top10_preds.columns:
                y_proba = top10_preds["probability"]
            else:
                y_proba = top10_preds["prediction"].astype(float)

            generate_classification_report(
                y_true=top10_preds["actual"],
                y_pred=top10_preds["prediction"],
                y_proba=y_proba,
                model_name="Top-10 Classifier",
                output_path=reports_dir / "evidently_top10.html"
            )
        else:
            logger.warning(f"Top-10 predictions not found at {top10_preds_path}")
            logger.warning("Run evaluation first: make evaluate")
    except Exception as e:
        logger.error(f"Failed to generate Top-10 report: {e}")

    try:
        if dnf_preds_path.exists():
            logger.info("Generating DNF classification report...")
            dnf_preds = pd.read_csv(dnf_preds_path)

            # Handle single-class case
            if "probability" in dnf_preds.columns:
                y_proba = dnf_preds["probability"]
            else:
                y_proba = dnf_preds["prediction"].astype(float)

            generate_classification_report(
                y_true=dnf_preds["actual"],
                y_pred=dnf_preds["prediction"],
                y_proba=y_proba,
                model_name="DNF Classifier",
                output_path=reports_dir / "evidently_dnf.html"
            )
        else:
            logger.warning(f"DNF predictions not found at {dnf_preds_path}")
            logger.warning("Run evaluation first: make evaluate")
    except Exception as e:
        logger.error(f"Failed to generate DNF report: {e}")

    # Generate drift report
    try:
        logger.info("Generating data drift report...")
        generate_drift_report(
            train_df=train_df,
            test_df=test_df,
            feature_cols=feature_cols,
            output_path=reports_dir / "evidently_drift.html"
        )
    except Exception as e:
        logger.error(f"Failed to generate drift report: {e}")

    logger.info("=" * 60)
    logger.info("EVIDENTLY REPORTS COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Reports saved to: {reports_dir}")
    logger.info("  - evidently_top10.html")
    logger.info("  - evidently_dnf.html")
    logger.info("  - evidently_drift.html")


def main():
    """CLI entry point for generating Evidently reports."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Evidently reports for model evaluation"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=f"Path to DuckDB database (default: {config.DUCKDB_PATH})"
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=None,
        help=f"Directory with trained models (default: {config.MODELS_DIR})"
    )
    parser.add_argument(
        "--features-dir",
        type=Path,
        default=None,
        help="Directory with exported features (default: data/features)"
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Directory to save reports (default: reports/)"
    )

    args = parser.parse_args()

    try:
        generate_all_reports(
            db_path=args.db_path,
            models_dir=args.models_dir,
            features_dir=args.features_dir,
            reports_dir=args.reports_dir
        )
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise


if __name__ == "__main__":
    main()
