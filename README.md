# IoT Appliance Sensor Pipeline (Medallion Architecture)
**Dataplatform Development lab and group project in the Data Engineering 2025 program at STI**

--- 
**An event-driven data engineering pipeline simulating a fleet of smart home appliances. It ingests, validates, and stores raw sensor data via Apache Kafka and PostgreSQL, implementing a Medallion Architecture (Bronze, Silver, Gold) to process and analyze machine wear and tear over time.**

## Features (v0.1.0 - Bronze Layer)

* **Stateful Fleet Simulator:** Generates continuous, logical telemetry data (RPM, temperature, vibration, run hours) for a static fleet of appliances, allowing for actual time-series analysis.

* **Chaos Engineering:** Intentionally injects technical faults (missing IDs, offline sensors), business anomalies (overheating engines), and ETL noise (whitespaces, malformed strings) into the data stream.

* **Quality Gate (Consumer):** Utilizes Pydantic for strict schema validation. Valid events are routed to a staging table, while corrupted data is caught and routed to a Dead Letter Queue (DLQ).

* **ELT Storage Pattern:** Stores the original JSON payload as `TEXT` in PostgreSQL to preserve ETL noise, enabling the Silver layer to perform realistic data cleaning.

## Tech Stack

* **Data Generation:** Python 3.12+, Faker
* **Message Broker:** Apache Kafka (Docker), `confluent-kafka`
* **Data Validation:** Pydantic
* **Database:** PostgreSQL (Docker), `psycopg`
* **Tooling:** `uv`, Git

---

## Project Structure

```text
iot_sensor_pipeline/
├── data/raw/             # Cold storage for generated JSONL source of truth
│
├── docs/                 # System Architecture Docs (CDM, LDM, PDM, Overviews)
│
├── src/
│   │└── producer/
│   │   └── producer.py   # Fleet simulator and Kafka producer (Bronze)      
│   └── consumer/      
│       └── consumer.py   # Quality gate and Postgres ingestion (Bronze)
│
├── .env.example          # Template for environment variables
├── docker-compose.yml    # Local infrastructure (Kafka, Zookeeper, PostgreSQL)
├── pyproject.toml        # Dependencies managed by uv
└── README.md

```

## Quickstart

### Prerequisites

* Docker / Docker Desktop
* `uv` installed

### 1) Clone & Configure Environment

```bash
git clone https://github.com/JohnnyHyytiainen/group_project_dataplatform.git
cd group_projet_dataplatform
cp .env.example .env

```

> Ensure your `.env` contains the correct database credentials and ports (e.g., `DB_PORT=5440` if running in sandbox mode).

### 2) Start Infrastructure (Kafka & PostgreSQL)

```bash
docker compose up -d

```

Check Docker Desktop or run `docker ps` to ensure both containers are healthy.

### 3) Install Dependencies

```bash
uv sync

```

### 4) Run the Bronze Layer Pipeline

Open two separate terminal windows.

**Terminal 1 (Start the Consumer / Quality Gate):**
This script will automatically establish the PostgreSQL tables (`staging_sensor_data` and `faulty_events`) and begin listening to the Kafka topic.

```bash
uv run python -m src.consumer.consumer

```

**Terminal 2 (Start the Producer / Fleet Simulator):**
This will build the fleet in memory and start streaming events to Kafka, including intentional anomalies.

```bash
uv run python -m src.producer.producer

```

---

## Architecture & Roadmap

### 🥉 Bronze Layer (Raw Ingestion) - *Completed*

* [x] Stateful data generation with "chaos injection"(creating mess on purpose) (`producer.py`)
* [x] Kafka topic streaming
* [x] Real-time Pydantic monitoring & DLQ routing (Failing gracefully into `faulty_events`) (`worker.py`)
* [x] Raw TEXT storage in PostgreSQL (`staging_sensor_data`) acting as our Single Source of Truth.
* [x] Stable handling of databas connection and environmental variables
* [x] Data Modeling for entire Database design. Bronze -> Silver -> Golden layers  

### 🥈 Silver Layer (Cleansed & Conformed) - *In Progress*

* [ ] Pure Python ETL batch job to extract raw_data from the Bronze staging table.  

* [ ] Clean injected formatting noise (.strip() whitespaces, standardize casing) without relying on Pandas.

* [ ] Soft-filtering: Handle missing engine_id by setting an is_valid = False flag instead of dropping data.

* [ ] Idempotent Delta Load into a strongly typed `silver_sensor_data` PostgreSQL table (`ON CONFLICT DO NOTHING` utilizing `NULLS NOT DISTINCT`).

* [ ] Export a curated backup to a Data Lake file (`cleaned_sensor_data.jsonl`).

### 🥇 Gold Layer (Curated & Aggregated) - *Planned*

* [ ] Design and implement a Dimensional Model / Star Schema (`FACT_SENSOR_READING`, `DIM_ENGINE`, `DIM_DATE`, etc)

* [ ] Strict SQL transformations (e.g, extracting only `WHERE is_valid = TRUE`).

* [ ] Calculate business KPIs and hard threshold flags (Maintenance, Temperature, Vibration warnings) directly in SQL.

* [ ] Build aggregated daily tables (`FACT_ENGINE_DAILY`) for optimized dashboard querying.

### 🚀 API Layer (Serving) - Planned
* [ ] Build a FastAPI backend to serve curated data from the Medallion architecture.

* [ ] Implement pagination, connection pooling, and dynamic query filtering.

* [ ] Protect endpoints with Pydantic response models and comprehensive unit testing.

--- 

## Documentation

Check the `docs/` folder for comprehensive system architecture details:

* **[Bronze Layer Module Overview](docs/diagrams/architecture_flow.png)**
* **[Conceptual, Logical, and Physical Data Models](docs/diagrams/)**
* **[Module overview docs for Bronze layer(in swedish)](docs/module_overview_producer_consumer.md)**

---
