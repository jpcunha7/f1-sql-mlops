# Third-Party Licenses

This project uses the following open-source libraries and their respective licenses:

## Core Dependencies

### Data Processing

- **pandas** (BSD-3-Clause)
  https://github.com/pandas-dev/pandas
  Copyright (c) 2008-2011, AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team

- **pyarrow** (Apache-2.0)
  https://github.com/apache/arrow
  Copyright (c) 2016-2023 The Apache Software Foundation

- **duckdb** (MIT)
  https://github.com/duckdb/duckdb
  Copyright (c) 2018-2023 Stichting DuckDB Foundation

### Database & Transformation

- **dbt-core** (Apache-2.0)
  https://github.com/dbt-labs/dbt-core
  Copyright (c) 2016 Fishtown Analytics

- **dbt-duckdb** (Apache-2.0)
  https://github.com/duckdb/dbt-duckdb
  Copyright (c) 2022 DuckDB Labs

### Machine Learning

- **scikit-learn** (BSD-3-Clause)
  https://github.com/scikit-learn/scikit-learn
  Copyright (c) 2007-2023 The scikit-learn developers

- **mlflow** (Apache-2.0)
  https://github.com/mlflow/mlflow
  Copyright (c) 2018 Databricks, Inc.

### Data Quality & Monitoring

- **evidently** (Apache-2.0)
  https://github.com/evidentlyai/evidently
  Copyright (c) 2020-2023 EvidentlyAI, Inc.

### Web Application

- **streamlit** (Apache-2.0)
  https://github.com/streamlit/streamlit
  Copyright (c) 2018-2023 Snowflake Inc.

- **plotly** (MIT)
  https://github.com/plotly/plotly.py
  Copyright (c) 2016-2023 Plotly, Inc.

### Utilities

- **python-dotenv** (BSD-3-Clause)
  https://github.com/theskumar/python-dotenv
  Copyright (c) 2014, Saurabh Kumar

- **kaggle** (Apache-2.0)
  https://github.com/Kaggle/kaggle-api
  Copyright (c) 2018 Kaggle Inc.

- **pyyaml** (MIT)
  https://github.com/yaml/pyyaml
  Copyright (c) 2017-2021 Ingy döt Net, Copyright (c) 2006-2016 Kirill Simonov

## Development Dependencies

- **pytest** (MIT)
  https://github.com/pytest-dev/pytest
  Copyright (c) 2004-2023 Holger Krekel and pytest-dev team

- **ruff** (MIT)
  https://github.com/astral-sh/ruff
  Copyright (c) 2022 Charlie Marsh

- **ipython** (BSD-3-Clause)
  https://github.com/ipython/ipython
  Copyright (c) 2008-2014, IPython Development Team

- **jupyter** (BSD-3-Clause)
  https://github.com/jupyter/jupyter
  Copyright (c) 2001-2015, IPython Development Team

## License Summary

This project's dependencies use the following license types:
- **Apache-2.0**: 7 packages (dbt-core, dbt-duckdb, mlflow, evidently, streamlit, kaggle, pyarrow)
- **MIT**: 5 packages (duckdb, plotly, pyyaml, pytest, ruff)
- **BSD-3-Clause**: 4 packages (pandas, scikit-learn, python-dotenv, ipython, jupyter)

All licenses are permissive and compatible with the MIT license used by this project.

## Data License

The **Formula 1 World Championship (1950-2020)** dataset is provided by Kaggle:
- Source: https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020
- License: CC0: Public Domain / Kaggle Terms of Use
- This project does NOT redistribute the dataset
- Users must download data directly from Kaggle with their own credentials

## Additional Resources

For full license texts, see:
- Apache-2.0: https://www.apache.org/licenses/LICENSE-2.0
- MIT: https://opensource.org/licenses/MIT
- BSD-3-Clause: https://opensource.org/licenses/BSD-3-Clause

## Compliance

This project:
- ✅ Uses only permissive open-source licenses
- ✅ Provides attribution to all dependencies
- ✅ Does not redistribute proprietary data
- ✅ Maintains compatibility with MIT license
- ✅ Includes this notice in the repository

Last updated: 2024
