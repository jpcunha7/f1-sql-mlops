"""Generate synthetic toy dataset for CI/CD testing."""

import argparse
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from f1sqlmlops.config import config
from f1sqlmlops.logging_utils import setup_logger

logger = setup_logger(__name__)


def generate_toy_races(n_seasons: int = 7, races_per_season: int = 5, start_year: int = 2014) -> pd.DataFrame:
    """Generate synthetic races table."""
    data = []
    race_id = 1
    for year in range(start_year, start_year + n_seasons):
        for round_num in range(1, races_per_season + 1):
            data.append(
                {
                    "raceId": race_id,
                    "year": year,
                    "round": round_num,
                    "circuitId": (round_num % 3) + 1,
                    "name": f"Grand Prix {round_num}",
                    "date": f"{year}-{round_num:02d}-15",
                    "time": "14:00:00",
                }
            )
            race_id += 1
    return pd.DataFrame(data)


def generate_toy_drivers(n_drivers: int = 10) -> pd.DataFrame:
    """Generate synthetic drivers table."""
    data = []
    for i in range(1, n_drivers + 1):
        data.append(
            {
                "driverId": i,
                "driverRef": f"driver_{i}",
                "number": i,
                "code": f"DR{i:02d}",
                "forename": "Driver",
                "surname": f"{i}",
                "dob": f"199{i % 10}-01-01",
                "nationality": "Country",
            }
        )
    return pd.DataFrame(data)


def generate_toy_constructors(n_teams: int = 5) -> pd.DataFrame:
    """Generate synthetic constructors table."""
    data = []
    for i in range(1, n_teams + 1):
        data.append(
            {
                "constructorId": i,
                "constructorRef": f"team_{i}",
                "name": f"Team {i}",
                "nationality": "Country",
            }
        )
    return pd.DataFrame(data)


def generate_toy_circuits(n_circuits: int = 3) -> pd.DataFrame:
    """Generate synthetic circuits table."""
    data = []
    for i in range(1, n_circuits + 1):
        data.append(
            {
                "circuitId": i,
                "circuitRef": f"circuit_{i}",
                "name": f"Circuit {i}",
                "location": f"City {i}",
                "country": "Country",
                "lat": 50.0 + i,
                "lng": 4.0 + i,
                "alt": 100,
            }
        )
    return pd.DataFrame(data)


def generate_toy_status() -> pd.DataFrame:
    """Generate synthetic status table."""
    return pd.DataFrame(
        [
            {"statusId": 1, "status": "Finished"},
            {"statusId": 2, "status": "+1 Lap"},
            {"statusId": 3, "status": "Accident"},
            {"statusId": 4, "status": "Collision"},
            {"statusId": 5, "status": "Engine"},
        ]
    )


def generate_toy_qualifying(races_df: pd.DataFrame, drivers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic qualifying results."""
    data = []
    qualify_id = 1
    for _, race in races_df.iterrows():
        for position, (_, driver) in enumerate(drivers_df.iterrows(), 1):
            data.append(
                {
                    "qualifyId": qualify_id,
                    "raceId": race["raceId"],
                    "driverId": driver["driverId"],
                    "constructorId": (driver["driverId"] - 1) // 2 + 1,
                    "number": driver["number"],
                    "position": position,
                    "q1": f"1:{position + 20}.{position:03d}",
                    "q2": f"1:{position + 19}.{position:03d}" if position <= 15 else None,
                    "q3": f"1:{position + 18}.{position:03d}" if position <= 10 else None,
                }
            )
            qualify_id += 1
    return pd.DataFrame(data)


def generate_toy_results(
    races_df: pd.DataFrame, drivers_df: pd.DataFrame, status_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate synthetic race results."""
    data = []
    result_id = 1
    for _, race in races_df.iterrows():
        for idx, (_, driver) in enumerate(drivers_df.iterrows(), 1):
            # Simulate some DNFs
            dnf = idx > 8 and (idx + race["raceId"]) % 3 == 0
            status_id = 3 if dnf else 1  # Accident or Finished
            position = None if dnf else idx
            position_order = idx
            points = max(0, 26 - idx * 2) if not dnf and idx <= 10 else 0

            data.append(
                {
                    "resultId": result_id,
                    "raceId": race["raceId"],
                    "driverId": driver["driverId"],
                    "constructorId": (driver["driverId"] - 1) // 2 + 1,
                    "number": driver["number"],
                    "grid": idx,
                    "position": position,
                    "positionText": str(position) if position else "R",
                    "positionOrder": position_order,
                    "points": points,
                    "laps": 50 if not dnf else idx * 5,
                    "time": f"1:{idx + 30}:{idx:02d}.{idx:03d}" if not dnf else None,
                    "milliseconds": (90 + idx) * 60 * 1000 if not dnf else None,
                    "fastestLap": idx if not dnf else None,
                    "rank": idx if not dnf else None,
                    "fastestLapTime": f"1:{idx + 25}.{idx:03d}" if not dnf else None,
                    "fastestLapSpeed": 200 - idx if not dnf else None,
                    "statusId": status_id,
                }
            )
            result_id += 1
    return pd.DataFrame(data)


def generate_toy_seasons(races_df: pd.DataFrame) -> pd.DataFrame:
    """Generate synthetic seasons table."""
    years = sorted(races_df["year"].unique())
    return pd.DataFrame([{"year": year, "url": f"http://en.wikipedia.org/wiki/{year}_Formula_One_season"} for year in years])


def generate_toy_dataset(
    output_dir: Optional[Path] = None,
    n_seasons: int = 7,
    races_per_season: int = 5,
    n_drivers: int = 10
) -> None:
    """
    Generate complete synthetic toy dataset.

    Args:
        output_dir: Directory to save Parquet files
        n_seasons: Number of seasons to generate (default 7 for 2014-2020)
        races_per_season: Races per season
        n_drivers: Number of drivers
    """
    output_dir = output_dir or (config.DATA_DIR / "toy_parquet")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating toy dataset in: {output_dir}")
    logger.info(f"  Seasons: {n_seasons}, Races/season: {races_per_season}, Drivers: {n_drivers}")

    # Generate base tables (2014-2020 for train/val/test splits)
    races_df = generate_toy_races(n_seasons=n_seasons, races_per_season=races_per_season, start_year=2014)
    drivers_df = generate_toy_drivers(n_drivers=n_drivers)
    constructors_df = generate_toy_constructors(n_teams=5)
    circuits_df = generate_toy_circuits(n_circuits=3)
    status_df = generate_toy_status()

    # Generate derived tables
    qualifying_df = generate_toy_qualifying(races_df, drivers_df)
    results_df = generate_toy_results(races_df, drivers_df, status_df)
    seasons_df = generate_toy_seasons(races_df)

    # Save all tables
    tables = {
        "races": races_df,
        "drivers": drivers_df,
        "constructors": constructors_df,
        "circuits": circuits_df,
        "status": status_df,
        "qualifying": qualifying_df,
        "results": results_df,
        "seasons": seasons_df,
    }

    for table_name, df in tables.items():
        output_path = output_dir / f"{table_name}.parquet"
        table = pa.Table.from_pandas(df)
        pq.write_table(table, output_path, compression="snappy")
        logger.info(
            f"  ✓ {table_name}.parquet: {len(df)} rows, {len(df.columns)} columns"
        )

    logger.info(f"Toy dataset generated: {len(tables)} tables")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic toy dataset for testing"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.DATA_DIR / "toy_parquet",
        help="Directory to save toy Parquet files",
    )

    args = parser.parse_args()

    try:
        generate_toy_dataset(args.output_dir)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
