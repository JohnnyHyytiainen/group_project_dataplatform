# Module Overview: Data Lineage & Soft Deletes
*Written and updated 25/03-2026 by Johnny* 

**1. Data Lineage & Audit Trails**  
Data Lineage is not about the database managing itself; it is about **auditability and traceability**. If a stakeholder spots a 500°C anomaly in the BI dashboard for an engine in Stockholm, our architecture allows us to debug it in seconds:

1. We locate the anomaly in the Gold `FACT_SENSOR_READING` and identify its `silver_id`.

2. We trace `silver_id` back to the `silver_sensor_data` table to inspect the payload exactly as it looked after our cleaning pipeline processed it.

3. Using the timestamp, we can traverse all the way back to the Bronze `staging_sensor_data` to read the raw, unaltered Kafka JSON string to determine if the sensor actually transmitted "500" or if it was a network parsing error.

**2. Why We Avoid `ON DELETE CASCADE` (The Append-Only Mindset)**
In a traditional web application, `ON DELETE CASCADE` is incredibly useful. In a Data Warehouse (OLAP), it is a massive liability. If an engineer accidentally deletes an engine from `DIM_ENGINE`, a cascade rule would instantly wipe out three years of historical KPI data in the fact table, destroying enterprise financial statistics.

**Soft Deletes & SCDs:** Instead of physically deleting retired machines, we apply the concept of Slowly Changing Dimensions (SCD). By introducing boolean flags like `is_active = False` for dimensions (retired machines) or `is_valid = False` for facts (corrupted data), we preserve historical integrity while filtering the data out of active BI queries.