"""Train model to predict DNF (Did Not Finish) probability."""

import argparse
import pickle
import sys
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from f1sqlmlops.config import config
from f1sqlmlops.features.export_features import export_features, get_feature_columns
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)

TARGET = "target_dnf"
MODEL_NAME = "dnf_classifier"


def create_pipeline(n_estimators: int = 100, max_depth: int = 10) -> Pipeline:
    """
    Create scikit-learn pipeline for DNF classification.

    Args:
        n_estimators: Number of trees in random forest
        max_depth: Maximum depth of trees

    Returns:
        Scikit-learn Pipeline
    """
    # Preprocessing: impute missing values and scale
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline([
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ]), slice(None))  # Apply to all columns
        ]
    )

    # Random forest classifier
    classifier = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight='balanced',  # Handle class imbalance
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', classifier)
    ])

    return pipeline


def train_model(
    n_estimators: int = 100,
    max_depth: int = 10,
    db_path: Path = None,
    output_dir: Path = None
) -> Pipeline:
    """
    Train DNF prediction model with MLflow tracking.

    Args:
        n_estimators: Number of trees
        max_depth: Maximum tree depth
        db_path: Path to DuckDB database
        output_dir: Directory to save model

    Returns:
        Trained pipeline
    """
    output_dir = output_dir or config.MODELS_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set MLflow experiment
    mlflow.set_experiment("f1_dnf_prediction")

    with mlflow.start_run():
        logger.info("Starting DNF model training")

        # Log parameters
        mlflow.log_param("target", TARGET)
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("train_end_year", config.TRAIN_END_YEAR)
        mlflow.log_param("val_years", config.VAL_YEARS)

        # Load features
        logger.info("Loading features from DuckDB")
        splits = export_features(db_path)
        feature_cols, _ = get_feature_columns(splits['train'])

        # Prepare data
        X_train = splits['train'][feature_cols]
        y_train = splits['train'][TARGET]
        X_val = splits['val'][feature_cols]
        y_val = splits['val'][TARGET]

        logger.info(f"Training samples: {len(X_train):,}")
        logger.info(f"Validation samples: {len(X_val):,}")
        logger.info(f"Features: {len(feature_cols)}")

        # Log class distribution
        train_pos_pct = y_train.mean() * 100
        val_pos_pct = y_val.mean() * 100
        logger.info(f"Train DNF rate: {train_pos_pct:.1f}%")
        logger.info(f"Val DNF rate: {val_pos_pct:.1f}%")
        mlflow.log_metric("train_dnf_rate", train_pos_pct)
        mlflow.log_metric("val_dnf_rate", val_pos_pct)

        # Create and train pipeline
        logger.info("Training model...")
        pipeline = create_pipeline(n_estimators, max_depth)
        pipeline.fit(X_train, y_train)

        # Evaluate on training set
        y_train_pred = pipeline.predict(X_train)
        y_train_proba = pipeline.predict_proba(X_train)[:, 1]

        train_acc = accuracy_score(y_train, y_train_pred)
        train_auc = roc_auc_score(y_train, y_train_proba)
        train_logloss = log_loss(y_train, y_train_proba)

        logger.info(f"Train Accuracy: {train_acc:.4f}")
        logger.info(f"Train ROC-AUC: {train_auc:.4f}")
        logger.info(f"Train Log Loss: {train_logloss:.4f}")

        mlflow.log_metric("train_accuracy", train_acc)
        mlflow.log_metric("train_roc_auc", train_auc)
        mlflow.log_metric("train_log_loss", train_logloss)

        # Evaluate on validation set
        y_val_pred = pipeline.predict(X_val)
        y_val_proba = pipeline.predict_proba(X_val)[:, 1]

        val_acc = accuracy_score(y_val, y_val_pred)
        val_auc = roc_auc_score(y_val, y_val_proba)
        val_logloss = log_loss(y_val, y_val_proba)

        logger.info(f"Val Accuracy: {val_acc:.4f}")
        logger.info(f"Val ROC-AUC: {val_auc:.4f}")
        logger.info(f"Val Log Loss: {val_logloss:.4f}")

        mlflow.log_metric("val_accuracy", val_acc)
        mlflow.log_metric("val_roc_auc", val_auc)
        mlflow.log_metric("val_log_loss", val_logloss)

        # Classification report
        logger.info("\nValidation Classification Report:")
        report = classification_report(y_val, y_val_pred)
        logger.info(f"\n{report}")

        # Feature importance
        feature_importances = pipeline.named_steps['classifier'].feature_importances_
        feature_importance_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': feature_importances
        }).sort_values('importance', ascending=False)

        logger.info("\nTop 10 Most Important Features:")
        for idx, row in feature_importance_df.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        # Save feature importance
        importance_path = output_dir / f"{MODEL_NAME}_feature_importance.csv"
        feature_importance_df.to_csv(importance_path, index=False)
        mlflow.log_artifact(importance_path)

        # Save model
        model_path = output_dir / f"{MODEL_NAME}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(pipeline, f)
        logger.info(f"Model saved to {model_path}")

        # Log model to MLflow
        mlflow.sklearn.log_model(pipeline, MODEL_NAME)
        mlflow.log_artifact(model_path)

        # Save feature columns
        feature_cols_path = output_dir / f"{MODEL_NAME}_features.txt"
        with open(feature_cols_path, 'w') as f:
            f.write('\n'.join(feature_cols))
        mlflow.log_artifact(feature_cols_path)

        logger.info("Training complete!")

        return pipeline


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Train DNF prediction model"
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of trees in random forest"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum depth of trees"
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
        default=config.MODELS_DIR,
        help="Directory to save model"
    )

    args = parser.parse_args()

    try:
        train_model(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            db_path=args.db_path,
            output_dir=args.output_dir
        )
        sys.exit(0)

    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
