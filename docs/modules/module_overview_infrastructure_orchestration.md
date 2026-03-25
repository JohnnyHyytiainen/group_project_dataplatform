# Module Overview: Infrastructure & Orchestration (Docker)
*Written and updated 25/03-2026 by Johnny* 

## Purpose
To ensure our data platform is platform-agnostic, reproducible, and scalable, we have containerized the entire architecture. Instead of requiring team members (or stakeholders) to manually configure Python environments and start multiple scripts, everything is orchestrated via Docker Compose. This meets industry standards for portability and CI/CD readiness.

**Architecture & Networking**
We utilize an isolated, internal Docker network where our services communicate via DNS (container names) rather than `localhost`

**1. Infrastructure (Official Images)**
* **`postgres:16-alpine`**: The Database engine. We utilize a hidden volume `live_pg_data` to ensure data persistence even if the container is destroyed. Exposed locally on port `5439` for PgAdmin access.

* **`apache/kafka:latest`**: Our Message Broker. Runs in KRaft-mode (without Zookeeper) for a modern, lightweight setup. 

*(Note: While `latest` is generally an anti-pattern in production due to breaking changes, it was a conscious MVP decision for development velocity)*

**2. Applications (Custom Image via `Dockerfile`)**
We use a single, centralized `Dockerfile` (based on `python:3.12-slim`) for our entire codebase. It utilizes `uv` for dependency installation and leverages Docker Layer Caching for lightning-fast builds. In our Compose file, we spin up isolated instances of this image with different responsibilities:
* **`api`**: Hosts the FastAPI server.
* **`consumer`**: Subscribes to Kafka (`kafka:9092`) and ingests data into the Bronze layer.
* **`producer`**: Our data generator. Uses a **Bind Mount** (`./data:/app/data`) to mirror the Source of Truth `.jsonl` file directly to our local disk in real time.
* **`streamlit`**: Our interactive BI Dashboard.

**Operations & Commands**
* **Start the entire Medallion Platform:** `docker-compose up -d --build`
* **Rebuild a specific service (e.g., Producer):** `docker compose build --no-cache producer`
* **Stop and tear down the environment:** `docker-compose down`
* **Replay historical data (from Cold Storage):** `docker exec -it live_producer uv run python -m src.producer.replayer`
