# Module Overview: Bronze Layer (Ingestion & Staging)
*Written and updated 25/03-2026 by Johnny* 


## Summary & Objectives
The Bronze layer is the entry point of our Medallion Architecture. Its primary objective is to reliably ingest, stream, validate, and persist raw data from our IoT appliance fleet. The focus is entirely on high fault tolerance and secure storage, preserving the data in its original state for asynchronous transformation in the Silver layer.

## Why Synthetic Data? (The Controlled Experiment)
We actively chose to build a synthetic Data Generator rather than pulling from an external API. This is not a shortcut; it is a controlled experiment to definitively prove our pipeline's quality control:

1. **Reproducibility:** External APIs change payloads or impose rate limits without warning. Synthetic data guarantees deterministic, repeatable testing environments.

2. **Chaos Engineering:** We can purposefully inject Medallion-relevant anomalies (missing keys, corrupted whitespaces, extreme temperatures) to scientifically validate our Silver layer's cleaning capabilities.

3. **Demo Stability:** Absolute immunity against third-party network outages, expired auth tokens, or throttling during critical stakeholder presentations.

4. **Data Privacy:** Guaranteed compliance (GDPR), as no personally identifiable information (PII) is ever generated or processed.

## Component Architecture
1. **Data Generator `producer.py`:** A stateful fleet simulator that initializes 4,000 unique machines. It advances time logically `run_hours` and `timestamp` to enable historical wear-and-tear analysis. It deliberately injects technical errors (NULLs) and business alarms (high RPM) with a 20-40% probability. All data is also written to a local `jsonl` file acting as Cold Storage.

2. **Message Broker (Apache Kafka):** Handles the data stream asynchronously, decoupling the Producer and Consumer and absorbing massive data spikes without overwhelming the database.

3. **Quality Gate `consumer.py` & `sensor_schema.py`:** Subscribes to the Kafka topic and utilizes **Pydantic** for strict type checking. It routes clean data to the Staging table and catches corrupt payloads, routing them safely to the Dead Letter Queue (DLQ).

4. **Storage (PostgreSQL):** The landing zone `staging_sensor_data` stores the approved payload in a `TEXT` column to guarantee the raw, unstructured JSON survives ingestion for downstream processing.


