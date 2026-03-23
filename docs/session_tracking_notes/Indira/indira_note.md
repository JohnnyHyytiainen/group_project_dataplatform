# Session tracking notes - consumer.py (Indira)

## Thursday - Sunday 08/03-2026

```text
- Built consumer.py with Kafka integration and Pydantic validation
    - Done

- Added SensorEvent model with field validation
    - Done

- Added maintenance flagging: WARNING ≥4000h, CRITICAL ≥5000h
    - Done

- Added flags for engine temperature, RPM and vibration
    - Done

- Added Dead Letter Queue (faulty_events) for rejected events
    - Done

- Updated staging table to store raw JSON as TEXT for downstream ETL
    - Done

```

## Monday 09/03-2026 - Thursday 12/03-2026

### worker.py (consumer) — Architecture Refactor

```text
Spent time refactoring the consumer to properly follow Medallion architecture.
The main thing was demoting Pydantic from a gatekeeper to a warning system —>
dirty data now reaches Bronze.

- Pydantic now lives in its own inner try/except —> failures log to faulty_events but never stop Bronze ingestion
- Default status set before Pydantic runs so the INSERT never crashes on missing variables
- Renamed all _flag columns to _status across the board (maintenance_status, temperature_status etc.)
- Split the except blocks — JSONDecodeError and Exception are now separate, easier to debug
- Switched to manual Kafka commit (enable.auto.commit = False) — DB commits first, Kafka second, nothing gets lost if something crashes

```

## Friday 13/03-2026 - Monday 16/03-2026

```text
api_schemas.py — Data contracts for the API :

Built the Pydantic response models that Johnny's API uses to validate outgoing data.
Basically a mirror of our silver_sensor_data table as Python classes.

- SensorData, PaginationMetadata and PaginatedSensorResponse

test_api.py — Testing without Docker :

Built the full test suite for Johnny's API endpoints using FastAPI's dependency override system.
The whole point is these tests run without Docker, without PostgreSQL, without anything.

- Built MockCursor and MockConnection to replace the real DB connection
- Used try/finally in override_get_db_connection() so cleanup always runs even if a test crashes
- Fixed Pylance warning on __exit__ using *_ instead of named params
- Added teardown_module() at the bottom so the mock doesn't leak into other test files
- 8 tests total — root, health, sensors endpoint, filters, and input validation (422 errors)

Code reviews :

Reviewed Johnny's connection pool and main.py before approving his PR.

```

## Tuesday 17/03-2026 - Thursday 19/03-2026

```text
api_schemas.py — Data contracts for the API :

Built the Pydantic response models that Johnny's API uses to validate outgoing data.
Basically a mirror of our silver_sensor_data table as Python classes.

- SensorData, PaginationMetadata and PaginatedSensorResponse

test_api.py — Testing without Docker :

Built the full test suite for Johnny's API endpoints using FastAPI's dependency override system.
The whole point is these tests run without Docker, without PostgreSQL, without anything.

- Built MockCursor and MockConnection to replace the real DB connection
- Used try/finally in override_get_db_connection() so cleanup always runs even if a test crashes
- Fixed Pylance warning on __exit__ using *_ instead of named params
- Added teardown_module() at the bottom so the mock doesn't leak into other test files
- 8 tests total — root, health, sensors endpoint, filters, and input validation (422 errors)

Code reviews :

Reviewed Johnny's connection pool and main.py before approving his PR.

```

## Tuesday 17/03-2026 - Monday 23/03-2026

### Silver Layer — Sprint Demo Preparation

```text
Prepared the Silver layer for sprint demo. Focus was on making sure the full
Bronze -> Silver flow was stable, demonstrable and clean enough to present.

Wrote test_cleaner.py to cover the Silver layer cleaning logic.
- Tests revealed a bug in cleaner.py — incorrect handling of certain edge cases
- Also found a related issue in etl_job.py caused by the same root problem
- Discussed findings with Johnny — he located and fixed both files
- Johnny pushed the updated cleaner.py and etl_job.py to the repo

Built the dashboard components that connect our Gold layer to the Streamlit frontend.

- queries.py
This is where all the SQL lives for the dashboard. Every function just returns a SQL string that reads from our Gold star schema — the fact tables and dimension tables we built. I kept all the queries in one place so if something needs changing, you only have to touch one file instead of hunting through every page script.The queries cover everything the dashboard needs — fleet-wide KPIs, warning breakdowns by appliance type and city, temperature trends over the last 90 days, top offending engines, and maintenance health bands based on run hours.

- charts.py
All the Plotly chart functions live here. Each function takes a DataFrame and returns a chart — nothing else. No Streamlit code in here at all, which means the charts are reusable and easy to test independently. Same Separation of Concerns principle we used throughout the rest of the pipeline.Covers grouped bar charts, horizontal bars, a line chart for temperature trends, a donut chart for fleet health distribution, and a histogram for run hours.

- 01_overview.py and 02_anomalies.py
These are the actual dashboard pages. They connect to the database, call the query functions, check if there's data, and pass the results to the chart functions to display. Every section has an empty-data guard so the page shows a friendly message instead of crashing if the Gold layer has no data yet.

```
