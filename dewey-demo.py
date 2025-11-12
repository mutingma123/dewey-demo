import marimo

__generated_with = "0.17.7"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    import pathlib

    import duckdb
    import polars as pl
    return duckdb, mo, pathlib, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SafeGraph Data Loading

    This section loads and filters SafeGraph location data for a specific industry and country.

    **What is happening:**
    - We specify a target NAICS code (622110 - Hospital/medical facilities)
    - Load SafeGraph parquet data from external storage
    - Filter the dataset to only include locations matching the target industry AND located in the US
    - Extract the list of matching placekeys for use in downstream analysis

    The filtered data and placekey list are used to query related data from other datasets (Advan and Veraset).
    """)
    return


@app.cell
def _(pathlib, pl):
    target_naics_code = 622110

    safegraph_data_filepath = pathlib.Path('/media/nick/Extreme Pro/all_safegraph_data.parquet')
    assert safegraph_data_filepath.exists()

    naics_safegraph_data = pl.scan_parquet(
        safegraph_data_filepath
    ).filter(
        pl.col('naics_code') == target_naics_code,
        pl.col('iso_country_code') == 'US'
    ).collect()

    relevant_placekeys = naics_safegraph_data['placekey'].to_list()
    len(relevant_placekeys)
    return naics_safegraph_data, relevant_placekeys, safegraph_data_filepath


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Helper Functions

    This section defines utility functions used throughout the analysis.

    **execute_sql(database_filepath, sql):**
    - **Purpose:** Provides a reusable interface for executing SQL queries against DuckDB databases
    - **Parameters:**
      - `database_filepath`: Path to a DuckDB database file
      - `sql`: SQL query string to execute
    - **Returns:** Results as a Polars DataFrame
    - **Why:** Reduces code repetition and makes database queries more consistent across the notebook
    """)
    return


@app.cell
def _(duckdb, pathlib, pl):
    def execute_sql(
        database_filepath: pathlib.Path,
        sql: str,
    ) -> pl.DataFrame:

        with duckdb.connect(database_filepath) as _conn:
            database_data = _conn.execute(sql).pl()

        return database_data
    return (execute_sql,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Advan Demo

    This section demonstrates querying Advan mobility data for hospital locations and processing hourly visit patterns.

    **What is happening:**
    1. **Database Setup:** Locate and connect to the Advan DuckDB database
    2. **SQL Query:** Retrieve specific columns (placekey, date ranges, and hourly visit data) for locations matching our target hospital placekeys
    3. **Data Transformation:**
       - Parse JSON-encoded visit counts from strings into lists of integers
       - Calculate visit proportions (normalized visit counts as fractions)
       - Generate hourly datetime ranges matching the visit data
       - Explode rows so each hour gets its own row with corresponding visit count and proportion
    4. **Result:** A granular dataset with one row per hour per location, enabling time-series analysis of hospital foot traffic

    This approach converts aggregate weekly patterns into hourly-level data points suitable for detailed analysis.
    """)
    return


@app.cell
def _(duckdb, execute_sql, pathlib, pl, relevant_placekeys):
    advan_database_directory = pathlib.Path('/media/nick/Extreme Pro/advan_databases/')
    assert advan_database_directory.exists()

    advan_database_filepaths = list(advan_database_directory.glob('*duckdb'))

    advan_database_filepath = advan_database_filepaths[0]

    advan_table_info = execute_sql(
        database_filepath=advan_database_filepath, 
        sql='SHOW ALL TABLES',
    )

    columns_to_keep = [
      "placekey",
      "date_range_start",
      "date_range_end",
      "visits_by_each_hour",
      "date",
      "part"
    ]
    columns_to_keep_string = ', '.join(columns_to_keep)

    placeholders = ', '.join(['?'] * len(relevant_placekeys))
    sql_statement = f"SELECT {columns_to_keep_string} FROM advan_weekly_patterns WHERE placekey IN ({placeholders})"

    with duckdb.connect(advan_database_filepath) as _conn:
        hospital_data = _conn.execute(sql_statement, relevant_placekeys).pl()

    hospital_data = hospital_data.sort(
        'placekey'
    )

    hospital_data = hospital_data.with_columns(
        pl.col('visits_by_each_hour').str.json_decode(pl.List(pl.Int64))
    ).with_columns(
        visit_proportions = pl.col('visits_by_each_hour')/pl.col('visits_by_each_hour').list.sum()
    ).with_columns(
        datetime = pl.datetime_ranges(
            start='date_range_start',
            end='date_range_end',
            interval='1h',
            closed='left'
        )
    ).drop_nulls(
        'visits_by_each_hour'
    ).explode([
        'visits_by_each_hour',
        'visit_proportions',
        'datetime',
    ])
    return (hospital_data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Joining Advan and SafeGraph

    This section combines Advan mobility data with SafeGraph location attributes.

    **What is happening:**
    - Performs an **inner join** on the `placekey` column to match hospital visit records with their location details
    - From SafeGraph, we extract:
      - `placekey`: The common identifier for matching records
      - `postal_code`: Geographic location information for analysis
      - `location_name`: Human-readable hospital names
    - **Result:** Each hourly visit record now includes context about which hospital it represents and its location

    This enriched dataset can be used for location-based analysis or filtering by specific hospitals or regions.
    """)
    return


@app.cell
def _(hospital_data, naics_safegraph_data):
    hospital_data.join(
        naics_safegraph_data.select([
            'placekey',
            'postal_code',
            'location_name'
        ]),
        on='placekey',
        how='inner',
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Veraset Demo

    This section demonstrates querying Veraset device-level mobility data and enriching it with location information.

    **What is happening:**
    1. **Database Setup:** Locate and connect to the Veraset DuckDB database
    2. **First Query - Hospital Devices:** Find all device CAIDs (consumer anonymous IDs) that visited our target hospitals
       - Filter `veraset_visits` to only include records with safegraph_place_ids matching our hospital locations
       - Extract unique device IDs (CAIDs) for further analysis
    3. **Second Query - Device History:** Get the complete visit history for those devices
       - Query all visits made by those CAIDs (regardless of location)
       - Retrieve timestamp and location data for each visit
    4. **Enrichment:** Join visit data with full SafeGraph location details
       - Combine Veraset device visit timestamps with SafeGraph location attributes (names, postal codes, etc.)
       - This allows analysis of where people who visited target hospitals also visited

    **Use Case:** Understand device mobility patterns - where did people go before/after visiting hospitals?
    """)
    return


@app.cell
def _(
    duckdb,
    execute_sql,
    naics_safegraph_data,
    pathlib,
    pl,
    safegraph_data_filepath,
):
    veraset_database_directory = pathlib.Path('/media/nick/Extreme Pro/veraset_databases/')
    assert veraset_database_directory.exists()

    veraset_database_filepaths = list(veraset_database_directory.glob('*duckdb'))

    veraset_database_filepath = veraset_database_filepaths[0]

    veraset_table_info = execute_sql(
        database_filepath=veraset_database_filepath, 
        sql='SHOW ALL TABLES',
    )

    relevant_safegraph_ids = naics_safegraph_data['safegraph_place_id'].to_list()

    veraset_placeholders = ', '.join(['?'] * len(relevant_safegraph_ids))
    veraset_sql_statement = f"SELECT caid, safegraph_place_id FROM veraset_visits WHERE safegraph_place_id IN ({veraset_placeholders})"

    with duckdb.connect(veraset_database_filepath) as _conn:
        veraset_hospital_data = _conn.execute(veraset_sql_statement, relevant_safegraph_ids).pl()

    relevant_caids = veraset_hospital_data['caid'].unique().to_list()


    veraset_caid_placeholders = ', '.join(['?'] * len(relevant_caids))
    veraset_caid_sql_statement = f"SELECT local_timestamp, caid, safegraph_place_id FROM veraset_visits WHERE caid IN ({veraset_caid_placeholders})"

    with duckdb.connect(veraset_database_filepath) as _conn:
        veraset_caid_data = _conn.execute(veraset_caid_sql_statement, relevant_caids).pl()

    all_safegraph_data = pl.scan_parquet(
        safegraph_data_filepath
    ).filter(
        pl.col('iso_country_code') == 'US'
    ).collect()

    veraset_caid_data.join(
        all_safegraph_data,
        on='safegraph_place_id',
        how='inner',
    )
    return


if __name__ == "__main__":
    app.run()
