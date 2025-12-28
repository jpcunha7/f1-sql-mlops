"""DuckDB warehouse utilities for managing database connections and views."""

from pathlib import Path
from typing import Optional

import duckdb

from f1sqlmlops.config import config
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


def get_connection(db_path: Optional[Path] = None) -> duckdb.DuckDBPyConnection:
    """
    Create or get a DuckDB connection.

    Args:
        db_path: Path to DuckDB file (defaults to config)

    Returns:
        DuckDB connection object
    """
    db_path = db_path or config.DUCKDB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Connecting to DuckDB: {db_path}")
    return duckdb.connect(str(db_path))


def register_parquet_views(
    conn: duckdb.DuckDBPyConnection,
    parquet_dir: Optional[Path] = None,
) -> None:
    """
    Register Parquet files as views in DuckDB.

    Creates views named raw_<table> for each Parquet file.

    Args:
        conn: DuckDB connection
        parquet_dir: Directory containing Parquet files
    """
    parquet_dir = parquet_dir or config.PARQUET_DIR

    if not parquet_dir.exists():
        logger.warning(f"Parquet directory not found: {parquet_dir}")
        return

    parquet_files = sorted(parquet_dir.glob("*.parquet"))

    if not parquet_files:
        logger.warning(f"No Parquet files found in {parquet_dir}")
        return

    logger.info(f"Registering {len(parquet_files)} Parquet files as views")

    for parquet_file in parquet_files:
        table_name = parquet_file.stem
        view_name = f"raw_{table_name}"

        # Use absolute path to ensure views work from any directory
        absolute_path = parquet_file.resolve()

        # Create or replace view
        query = f"""
        CREATE OR REPLACE VIEW {view_name} AS
        SELECT * FROM read_parquet('{absolute_path}')
        """

        try:
            conn.execute(query)
            logger.info(f"  ✓ {view_name}")
        except Exception as e:
            logger.error(f"  ✗ Failed to create {view_name}: {e}")


def execute_query(
    conn: duckdb.DuckDBPyConnection, query: str, description: str = ""
):
    """
    Execute a SQL query with logging.

    Args:
        conn: DuckDB connection
        query: SQL query to execute
        description: Optional description for logging

    Returns:
        Query result
    """
    if description:
        logger.info(f"Executing: {description}")

    try:
        result = conn.execute(query).fetchall()
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise


def inspect_warehouse(db_path: Optional[Path] = None) -> None:
    """
    Inspect warehouse contents and print summary.

    Args:
        db_path: Path to DuckDB file
    """
    conn = get_connection(db_path)

    # Get all tables and views
    tables = conn.execute(
        "SELECT table_name, table_type FROM information_schema.tables "
        "WHERE table_schema = 'main'"
    ).fetchall()

    logger.info("Warehouse contents:")
    for table_name, table_type in sorted(tables):
        # Get row count
        try:
            count = conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            logger.info(f"  {table_type}: {table_name} ({count:,} rows)")
        except Exception:
            logger.info(f"  {table_type}: {table_name}")

    conn.close()


def main():
    """CLI entry point to register Parquet views."""
    logger.info("Registering Parquet views in DuckDB warehouse")
    conn = get_connection()
    register_parquet_views(conn)
    conn.close()
    logger.info("Parquet views registered successfully")


if __name__ == "__main__":
    main()
