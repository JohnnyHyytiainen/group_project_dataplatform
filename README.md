# IoT Appliance Sensor Pipeline (Medallion Architecture)

> **Data Platform Development Lab & Group Project** > *Data Engineering 2025 Program at STI (Stockholm)*

An event-driven data engineering platform simulating a fleet of smart home appliances. It ingests, validates, and stores raw sensor data via Apache Kafka and PostgreSQL, implementing a strict Medallion Architecture (Bronze, Silver, Gold). The platform is designed to process streaming telemetry, catch physical machine faults, and serve analytical data for predictive maintenance dashboards.

---

## Business Value & Core Pillars
This platform translates raw IoT telemetry into actionable operational insights through four core pillars:

1. **Streaming Ingestion (Apache Kafka):** *From Reactive to Proactive.* We ingest real-time telemetry to detect anomalies instantly, rather than waiting for customer breakdown reports.

2. **Medallion Architecture:** *Trust in Data.* By enforcing strict Pydantic quality gates across decoupled layers (Bronze, Silver, Gold), we guarantee that our BI dashboards reflect a 100% accurate, noise-free single source of truth.

3. **Infrastructure as Code (Docker & CI/CD):** *Disaster Recovery & Portability.* The entire platform is containerized and validated by GitHub Actions. If a server goes down, the environment can be fully restored in minutes.

4. **Database Migrations (Alembic):** *Safe Evolution.* We manage our PostgreSQL schemas with Alembic, enabling zero-downtime upgrades and instant rollbacks to protect historical data integrity.

---

## Tech Stack

* **Data Generation:** Python 3.12+, Faker
* **Message Broker:** Apache Kafka (Docker/KRaft)
* **Ingestion & ETL:** `confluent-kafka`, `psycopg` (v3)
* **Data Validation:** Pydantic
* **Database & Migrations:** PostgreSQL 16, Alembic
* **Serving & Visualization:** FastAPI, Streamlit
* **DevOps:** Docker Compose, `uv`, GitHub Actions, Ruff, Pytest

---

## Project Structure

```text
iot_sensor_pipeline/
├── alembic/                # Database migration scripts & history
├── data/
│   ├── raw/                # Cold storage for generated JSONL source of truth
│   └── processed/          # Silver layer backups
├── docs/                   # Architecture Docs (CDM, LDM, PDM, Overviews)
│   ├── diagrams/           # Visual representations of data flow
│   └── modules/            # Deep dives into Business Value & Technical decisions
├── src/
│   ├── api/                # FastAPI backend with connection pooling
│   ├── config/             # Centralized environment variable management
│   ├── consumer/           # Kafka Consumer & Bronze ingestion (Quality Gate)
│   ├── dashboard/          # Streamlit UI (Overview, Anomalies, Errors)
│   ├── gold/               # Star Schema ETL & Daily Aggregations
│   ├── producer/           # Stateful Fleet simulator & Kafka producer
│   ├── schemas/            # Global Pydantic data contracts
│   ├── silver/             # Idempotent cleaning & structural transformations
│   └── test/               # Pytest suite for API and Data Validation
├── .env.example            # Template for environment variables
├── docker-compose.yml      # Local infrastructure orchestration
├── Dockerfile              # Unified, optimized Python image
└── pyproject.toml          # Dependencies managed by uv
```


## Quickstart

### Prerequisites

  * Docker / Docker Desktop
  * `uv` (Fast Python package manager) installed

### 1\. Clone & Configure Environment


- git clone [https://github.com/JohnnyHyytiainen/group_project_dataplatform](https://github.com/JohnnyHyytiainen/group_project_dataplatform)
- cd group_project_dataplatform
- cp .env.example .env


*(Ensure your `.env` contains the correct database credentials).*

### 2\. Start the Data Platform (Orchestration)

Spin up the entire Medallion Architecture (PostgreSQL, Kafka, API, Consumer, Producer, and Dashboard) with a single command:

```bash
docker compose up -d --build
```

> **Note:** The Producer will automatically start simulating the 1,200 machine fleet, and the Consumer will begin ingesting into the Bronze layer.

### 3\. Access the Interfaces

  * **Streamlit BI Dashboard:** `http://localhost:8501`
  * **FastAPI Swagger UI:** `http://localhost:8000/docs`

### 4\. Database Migrations (Alembic)

To ensure your database structure is up to date with the latest code, run:

```bash
uv run alembic upgrade head
```

*(To tear down the environment and wipe the database volumes, run `docker compose down -v`)*

-----

## Architecture & Roadmap

### Bronze Layer (Raw Ingestion) - *Completed*

  * [x] **Stateful Data Generation:** Simulates continuous wear-and-tear `run_hours` with Chaos Engineering (intentional anomalies)

  * [x] **Event Streaming:** Decoupled architecture using Apache Kafka.

  * [x] **Quality Gate:** Real-time Pydantic validation routing corrupt data to a Dead Letter Queue `faulty_events`.

  * [x] **ELT Storage:** Preserves raw JSON payloads as `TEXT` in PostgreSQL.

### Silver Layer (Cleansed & Conformed) - *Completed*

  * [x] **Pure Python ETL:** Extracts raw Bronze data without relying on heavy frameworks like Pandas.

  * [x] **Data Cleaning:** Strips whitespace, standardizes casing, and handles missing IDs using soft-filtering `is_valid` flags.

  * [x] **Idempotent Upserts:** Ensures no duplicate data via `ON CONFLICT DO NOTHING`.

  * [x] **Database Versioning:** Schema managed securely via Alembic.

### Gold Layer (Curated & Aggregated) - *Completed*

  * [x] **Dimensional Modeling:** Implemented a strict Star Schema `FACT_SENSOR_READING`, `DIM_ENGINE`, `DIM_LOCATION`, etc.

  * [x] **Business Logic in SQL:** Calculates physical machine faults Maintenance, Temperature, RPM, Vibration warnings.

  * [x] **BI Integration:** Connects seamlessly to Streamlit for real-time Executive Dashboards.

### API Layer (Serving) - *Completed*

  * [x] **FastAPI Backend:** Serves clean data with built-in DDoS protection (Pagination).
  * [x] **Connection Pooling:** Uses `psycopg_pool` managed via `@asynccontextmanager` to prevent database overloading.
  * [x] **Dynamic Filtering:** `WHERE 1=1` implementation for flexible query parameters.

-----

## Documentation

For a deep dive into our engineering decisions, please explore the `docs/` folder:

  * **[Bronze Layer Architecture & Setup](docs/modules/module_overview_bronze_layer.md)**
  * **[Database Design & Medallion Philosophy](docs/modules/module_overview_database_architecture_design.md)**
  * **[Data Lineage & Soft Deletes](docs/modules/module_overview_database_lineage.md)**
  * **[Database Migrations with Alembic](docs/modules/module_overview_db_migration_alembic.md)**
  * **[CI/CD with GitHub Actions](docs/modules/module_overview_CICD_github_actions.md)**
  * **[API Core & Connection Pooling](docs/modules/module_overview_api.md)**

### ERDs and Visuals
* **[Bronze Layer Flowchart overview](docs/diagrams/architecture_BRONZE.png)**
* **[Silver Layer Flowchart overview](docs/diagrams/architecture_SILVER.png)**
* **[Conceptual, Logical, and Physical Data Models for Bronze, Silver, Gold layers](docs/diagrams/)**


---
