# Contributing to F1 SQL MLOps

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites
- Python 3.11 or 3.12
- Git
- Make
- Kaggle API credentials (for real data)

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/f1-sql-mlops.git
cd f1-sql-mlops
```

2. Set up development environment:
```bash
make setup
source venv/bin/activate
```

3. Generate toy data for development:
```bash
python -m f1sqlmlops.ingestion.generate_toy_data
python -m f1sqlmlops.warehouse.duckdb_utils
cd dbt && dbt build --profiles-dir .
```

## Development Workflow

### Code Quality

Before committing, ensure your code passes all quality checks:

```bash
# Run linter
make lint

# Run tests
make test

# Auto-fix linting issues
ruff check --fix src/ tests/
```

### Testing

We use pytest for testing. Tests are organized by module:

- `tests/test_toy_data.py` - Data generation tests
- `tests/test_schema_checks.py` - Schema validation tests
- `tests/test_features.py` - Feature engineering tests
- `tests/test_training.py` - Model training smoke tests
- `tests/test_config.py` - Configuration tests

Run specific test files:
```bash
pytest tests/test_toy_data.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=f1sqlmlops --cov-report=html
```

### Adding New Features

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following the project structure:
   - Data ingestion: `src/f1sqlmlops/ingestion/`
   - dbt models: `dbt/models/`
   - Training: `src/f1sqlmlops/training/`
   - Inference: `src/f1sqlmlops/inference/`

3. **Write tests** for your changes in `tests/`

4. **Update documentation** if needed

5. **Commit with descriptive messages:**
```bash
git commit -m "feat: add new feature X"
git commit -m "fix: resolve issue with Y"
git commit -m "docs: update README for Z"
```

6. **Push and create a pull request:**
```bash
git push origin feature/your-feature-name
```

## Code Style

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for functions and classes

Example:
```python
def predict_race(
    features: pd.DataFrame,
    models: dict,
    feature_cols: list
) -> pd.DataFrame:
    """
    Generate predictions for a race.

    Args:
        features: DataFrame with race features
        models: Dictionary of trained models
        feature_cols: List of feature column names

    Returns:
        DataFrame with predictions and probabilities
    """
    # Implementation
```

### SQL Style (dbt)

- Use lowercase for SQL keywords in dbt models
- Use CTE (Common Table Expressions) for clarity
- Add comments for complex logic
- Use 4-space indentation

Example:
```sql
with source as (
    select * from {{ source('raw', 'raw_races') }}
),

renamed as (
    select
        "raceId" as race_id,
        year,
        round
    from source
)

select * from renamed
```

## Pull Request Process

1. **Ensure all tests pass** in CI
2. **Update documentation** if you're changing user-facing features
3. **Add entry to CHANGELOG.md** (if applicable)
4. **Request review** from maintainers
5. **Address review feedback** promptly

### PR Checklist

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages follow conventions

## Reporting Issues

### Bug Reports

When reporting bugs, include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

### Feature Requests

For feature requests, describe:
- The problem you're trying to solve
- Proposed solution
- Alternative solutions considered
- Additional context

## Architecture Guidelines

### Data Flow

```
Kaggle → CSV → Parquet → DuckDB → dbt → Features → Models → Predictions
```

### Anti-Leakage Rules

**Critical:** Features must only use information available BEFORE the race.

✅ Allowed:
- Qualifying position
- Driver stats from previous races
- Circuit historical data

❌ Not allowed:
- Lap times from target race
- Final position from target race
- Pit stops from target race

### Temporal Splits

- Training: years ≤ 2016
- Validation: 2017-2018
- Test: 2019-2020

Ensure any new features maintain these splits.

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. GitHub Actions will build and publish

## Questions?

- Open an issue for questions
- Check existing issues and documentation
- Review closed PRs for examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
