"""Evaluate trained models on test set."""

import argparse
import pickle
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
)

from f1sqlmlops.config import config
from f1sqlmlops.features.export_features import export_features, get_feature_columns
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


def load_model(model_path: Path):
    """
    Load a trained model from pickle file.

    Args:
        model_path: Path to .pkl file

    Returns:
        Trained model/pipeline
    """
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str
) -> tuple[Dict, pd.DataFrame]:
    """
    Evaluate model and return metrics.

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        model_name: Name of model for logging

    Returns:
        Tuple of (metrics dictionary, predictions DataFrame)
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Evaluating {model_name}")
    logger.info(f"{'='*60}")

    # Make predictions
    y_pred = model.predict(X_test)
    y_proba_raw = model.predict_proba(X_test)

    # Handle case where only one class is present
    if y_proba_raw.shape[1] == 1:
        logger.warning("Only one class present in predictions")
        y_proba = y_proba_raw[:, 0]
    else:
        y_proba = y_proba_raw[:, 1]

    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred)
    }

    # ROC-AUC and log loss require both classes
    if len(y_test.unique()) > 1 and y_proba_raw.shape[1] == 2:
        metrics['roc_auc'] = roc_auc_score(y_test, y_proba)
        metrics['log_loss'] = log_loss(y_test, y_proba)
    else:
        metrics['roc_auc'] = 1.0
        metrics['log_loss'] = 0.0

    logger.info(f"Test Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Test ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Test Log Loss: {metrics['log_loss']:.4f}")

    # Classification report
    logger.info("\nClassification Report:")
    report = classification_report(y_test, y_pred)
    logger.info(f"\n{report}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    logger.info("\nConfusion Matrix:")
    if cm.shape == (2, 2):
        logger.info("                Predicted Negative  Predicted Positive")
        logger.info(f"Actual Negative      {cm[0, 0]:6d}            {cm[0, 1]:6d}")
        logger.info(f"Actual Positive      {cm[1, 0]:6d}            {cm[1, 1]:6d}")
    else:
        logger.info("Only one class present - confusion matrix not applicable")

    # Precision-Recall curve stats
    precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
    logger.info(f"\nPrecision at 50% threshold: {precision[len(precision)//2]:.4f}")
    logger.info(f"Recall at 50% threshold: {recall[len(recall)//2]:.4f}")

    # Create predictions DataFrame for Evidently
    predictions_df = pd.DataFrame({
        'actual': y_test.values,
        'prediction': y_pred,
        'probability': y_proba
    })

    return metrics, predictions_df


def evaluate_all_models(
    db_path: Path = None,
    models_dir: Path = None
) -> Dict[str, Dict]:
    """
    Evaluate all trained models on test set.

    Args:
        db_path: Path to DuckDB database
        models_dir: Directory containing trained models

    Returns:
        Dictionary of model names to metrics
    """
    models_dir = models_dir or config.MODELS_DIR
    models_dir = Path(models_dir)

    # Create reports directory
    reports_dir = config.PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load test data
    logger.info("Loading test data from DuckDB")
    splits = export_features(db_path)
    feature_cols, target_cols = get_feature_columns(splits['test'])

    X_test = splits['test'][feature_cols]
    logger.info(f"Test samples: {len(X_test):,}")
    logger.info(f"Test years: {splits['test']['year'].min()}-{splits['test']['year'].max()}")

    # Evaluate each model
    results = {}

    # Top-10 model
    top10_model_path = models_dir / "top10_classifier.pkl"
    if top10_model_path.exists():
        top10_model = load_model(top10_model_path)
        y_test_top10 = splits['test']['target_top_10']
        logger.info(f"Top-10 test positive rate: {y_test_top10.mean()*100:.1f}%")
        metrics, predictions = evaluate_model(
            top10_model, X_test, y_test_top10, "Top-10 Classifier"
        )
        results['top10'] = metrics

        # Save predictions for Evidently
        predictions_path = reports_dir / "top10_test_predictions.csv"
        predictions.to_csv(predictions_path, index=False)
        logger.info(f"✓ Top-10 predictions saved to {predictions_path}")
    else:
        logger.warning(f"Top-10 model not found at {top10_model_path}")

    # DNF model
    dnf_model_path = models_dir / "dnf_classifier.pkl"
    if dnf_model_path.exists():
        dnf_model = load_model(dnf_model_path)
        y_test_dnf = splits['test']['target_dnf']
        logger.info(f"DNF test rate: {y_test_dnf.mean()*100:.1f}%")
        metrics, predictions = evaluate_model(
            dnf_model, X_test, y_test_dnf, "DNF Classifier"
        )
        results['dnf'] = metrics

        # Save predictions for Evidently
        predictions_path = reports_dir / "dnf_test_predictions.csv"
        predictions.to_csv(predictions_path, index=False)
        logger.info(f"✓ DNF predictions saved to {predictions_path}")
    else:
        logger.warning(f"DNF model not found at {dnf_model_path}")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("EVALUATION SUMMARY")
    logger.info(f"{'='*60}")

    for model_name, metrics in results.items():
        logger.info(f"\n{model_name.upper()}:")
        for metric_name, value in metrics.items():
            logger.info(f"  {metric_name}: {value:.4f}")

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate trained models on test set"
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

    args = parser.parse_args()

    try:
        results = evaluate_all_models(args.db_path, args.models_dir)

        if not results:
            logger.error("No models found to evaluate")
            sys.exit(1)

        sys.exit(0)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
