# Module Overview: Database Design & Medallion Architecture
*Written and updated 25/03-2026 by Johnny* 

**Is a Database Without Foreign Keys Broken?**
In traditional software engineering (OLTP), yes. In Data Engineering and the Medallion Architecture, absolutely not. Here is the architectural reasoning behind our database design:

**1. Separation of Concerns (Decoupled Layers)**
The core philosophy of the Medallion Architecture is that layers (Bronze, Silver, Gold) must be decoupled. If we enforce a hard Foreign Key from Silver to Bronze e.g., `REFERENCES staging_sensor_data(id)`, we could never purge old data from Bronze without first deleting it from Silver. In reality, Staging environments are often purged after 30 days to save compute costs, while Silver and Gold retain historical data for years. Therefore, `bronze_id` in our Silver table is a **Soft Link (Lineage)**, providing traceability without restrictive database locks.

**2. The Dead Letter Queue (`faulty_events`)**
Our DLQ in the Bronze layer floats entirely in isolation. It is a dead end by design, a trash bin for corrupt payloads. No downstream tables depend on it, and it exists solely for operational debugging.

**3. Star Schema (Gold Layer)**
Unlike the decoupled upstream layers, the Gold layer is its own tightly bound ecosystem. Here, our `FACT_SENSOR_READING` table is strictly linked to our dimensions `DIM_ENGINE`, `DIM_DATE`, etc via Foreign Keys. This ensures absolute Referential Integrity for our BI Dashboards, while still only maintaining a soft lineage link `silver_id` back to the Silver layer.


**4. Single Database vs. Multiple Schemas**
For this MVP, we manage layer separation using table prefixes `staging_`, `silver_`, `dim_` within a single PostgreSQL database. In a larger enterprise setup, we would implement logical PostgreSQL Schemas `CREATE SCHEMA bronze;`. This elevates security through Role-Based Access Control (RBAC), allowing us to grant Data Analysts read-only access to the `gold` schema while completely hiding raw `bronze` data.