# Dewey Demo

An interactive data analysis and visualization application for exploring location intelligence and consumer mobility patterns across multiple enterprise data providers.

## Overview

Dewey Demo is a [marimo](https://marimo.io/) reactive notebook that demonstrates practical integration with three major location intelligence and mobility data platforms:

- **SafeGraph**: Geospatial data with industry classification (NAICS codes) for location discovery
- **Advan**: Weekly aggregated mobility metrics transformed into hourly-level time-series analytics
- **Veraset**: Device-level mobility tracking for understanding cross-location visit patterns

The application showcases how to load, transform, join, and analyze large-scale location intelligence datasets using modern Python data tools.

## Features

- 📍 **Location Filtering**: Query and filter locations by industry classification (NAICS codes)
- 📊 **Data Aggregation**: Transform weekly mobility data into hourly-level granularity using DuckDB
- 🔗 **Cross-Source Joins**: Combine data from multiple providers to create enriched datasets
- 📈 **Analytics**: Analyze foot traffic patterns and consumer mobility behavior
- 🎯 **Device Tracking**: Track individual devices across multiple location visits
- 🔄 **Reactive Execution**: Automatic dependency tracking and re-execution with marimo

## Technology Stack

- **Language**: Python 3.13+
- **Interactive Notebook**: [marimo](https://marimo.io/) - Reactive Python notebook framework
- **Data Processing**:
  - [Polars](https://www.pola.rs/) - Fast DataFrame operations
  - [PyArrow](https://arrow.apache.org/) - Apache Arrow data format support
  - [DuckDB](https://duckdb.org/) - SQL query engine for efficient data transformation
- **Visualization**: Matplotlib, Seaborn
- **Environment Management**: [Pixi](https://pixi.sh/) - Fast, reproducible Python environments

## Prerequisites

- **Pixi**: Install from [pixi.sh](https://pixi.sh/)
- **Git**: For cloning the repository
- **Data Access**: Credentials/API keys for SafeGraph, Advan, and Veraset (if you want to run against real data)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/nkfreeman/dewey-demo.git
cd dewey-demo
```

### 2. Install Pixi

If you haven't already installed Pixi, follow the [Pixi installation guide](https://pixi.sh/):

```bash
# On Linux or macOS with curl
curl -fsSL https://pixi.sh/install.sh | bash

# On Windows with Powershell
iwr -useb https://pixi.sh/install.ps1 | iex

# Via conda/mamba
conda install pixi -c conda-forge
```

### 3. Set Up the Python Environment

Pixi will automatically handle environment setup based on `pixi.toml`:

```bash
# Install all dependencies
pixi install

# This creates an isolated environment with all required packages
```

The environment includes:
- Python 3.13
- Marimo 0.17.7+
- Polars 1.35.1+
- DuckDB 1.4.1+
- PyArrow 22.0.0+
- Matplotlib, Seaborn, tqdm, and IPython

### 4. Run the Application

Start the interactive marimo notebook:

```bash
pixi run marimo edit dewey-demo.py
```

This launches the marimo editor in your default browser where you can interact with the notebook cells, modify code, and explore the data analysis workflows.

Alternatively, run the notebook in view-only mode:

```bash
pixi run marimo run dewey-demo.py
```

## Project Structure

```
dewey-demo/
├── dewey-demo.py              # Main marimo notebook (276 lines)
├── pixi.toml                  # Project configuration and dependencies
├── pixi.lock                  # Locked dependency versions (reproducible builds)
├── .gitignore                 # Git ignore rules
├── .gitattributes             # Git configuration for binary files
├── __marimo__/                # Marimo session cache and metadata
│   └── session/
│       ├── dewey-demo.py.json
│       └── advan-db-demo.py.json
└── README.md                  # This file
```

## Key Workflows

### 1. SafeGraph Data Loading
Filters US hospital locations by NAICS code (622110) and extracts placekeys for downstream analysis:

```python
# Example: Load SafeGraph locations and filter by NAICS code
sg_data = load_safegraph_data()
hospitals = sg_data.filter(pl.col('naics_code') == '622110')
```

### 2. Advan Analytics
Converts weekly aggregated mobility data into hourly-level time-series data:

```python
# Transform weekly metrics into hourly granularity
hourly_data = execute_sql("""
    SELECT
        date_trunc('hour', visit_date) as hour,
        COUNT(*) as visits
    FROM advan_data
    GROUP BY date_trunc('hour', visit_date)
""")
```

### 3. Veraset Device Tracking
Identifies devices that visited target locations and tracks their complete visit history:

```python
# Track device movements across all locations
device_visits = track_devices_across_locations(target_devices, location_inventory)
```

## Dependencies Management

### Adding New Dependencies

To add a new package to the project:

```bash
# Add a new dependency
pixi add package_name

# Or add to a specific project section
pixi add --pyproject package_name
```

This automatically updates `pixi.toml` and `pixi.lock`.

### Updating Dependencies

```bash
# Update all dependencies to the latest compatible versions
pixi update

# Update a specific package
pixi update package_name
```

### Viewing Installed Packages

```bash
pixi list
```

## Environment Variables

If your setup requires credentials for data access, create a `.env` file in the project root (ensure it's in `.gitignore`):

```bash
SAFEGRAPH_API_KEY=your_api_key
ADVAN_API_KEY=your_api_key
VERASET_API_KEY=your_api_key
```

Then load these in your notebook or scripts as needed.

## Development Workflow

### Activating the Environment Manually

If you prefer to work in the environment directly:

```bash
# Activate the pixi environment in your shell
eval "$(pixi shell-hook)"
pixi activate

# Now you can run Python directly
python -c "import marimo; print(marimo.__version__)"
```

### Running Commands with Pixi

Execute any command within the project environment:

```bash
pixi run python script.py
pixi run pip list
pixi run pytest tests/  # if you add tests
```

### Creating Custom Commands

Define shortcuts in `pixi.toml` for frequently used commands:

```toml
[tasks]
notebook = "marimo edit dewey-demo.py"
view = "marimo run dewey-demo.py"
```

Then run with: `pixi run notebook`

## Troubleshooting

### Environment Issues

```bash
# Clear and reinstall environment
rm -rf .pixi
pixi install

# Check environment status
pixi info
```

### Dependency Conflicts

If you encounter version conflicts:

```bash
# Update lock file with latest compatible versions
pixi update

# View detailed dependency tree
pixi graph
```

### Marimo Issues

```bash
# Reinstall marimo in the environment
pixi install --force marimo

# Check marimo installation
pixi run marimo --version
```

## Performance Notes

- **DuckDB**: Efficiently handles multi-GB parquet files with SQL queries
- **Polars**: Provides lazy evaluation and memory-efficient operations
- **PyArrow**: Enables efficient interoperability between different data formats
- **Marimo**: Automatic caching of cell outputs improves notebook responsiveness

## Learning Resources

- [Marimo Documentation](https://docs.marimo.io/)
- [Pixi Documentation](https://pixi.sh/latest/)
- [Polars Documentation](https://docs.pola.rs/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)

## Author

**nkfreeman** - [nkfreeman@cba.ua.edu](mailto:nkfreeman@cba.ua.edu)

## Repository

[GitHub: nkfreeman/dewey-demo](https://github.com/nkfreeman/dewey-demo)

## License

Check the repository for license information.

## Version

Current Version: **0.1.0** (Initial Release)

---

## Getting Help

- **Pixi Issues**: [pixi.sh GitHub](https://github.com/prefix-dev/pixi)
- **Marimo Issues**: [marimo GitHub](https://github.com/marimo-team/marimo)
- **Data Libraries**: See documentation links above

Happy exploring! 🚀
