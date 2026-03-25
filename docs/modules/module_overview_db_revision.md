# Module Overview: Database Migrations (Alembic)
*Written and updated 25/03-2026 by Johnny* 

## Alembic Theory & "Git for Databases"

Managing databases in a production environment without a migration tool is a ticking time bomb. Alembic acts as **Git for our database**. Just as we do not delete our entire codebase to add a new function, we cannot `DROP` our tables to add a new column. 

Alembic utilizes `ALTER TABLE` under the hood to sequentially modify the schema structure (adding "a window to the house") while leaving millions of rows of historical data completely untouched and secure.

## Business Value & Risk Mitigation
1. **Zero Data Loss:** We can dynamically inject new columns (e.g., `humidity`) into our Silver layer without risking the deletion of historical payloads.

2. **Eliminating Schema Drift:** In a collaborative team, Alembic ensures that every developer's local database schema is 100% synchronized with production via executable Python revision scripts.

3. **Instant Rollbacks:** If a flawed database update reaches production, we can execute `alembic downgrade -1` to instantly revert the schema to the last stable state, minimizing downtime.

**Schema vs. Data Flow**
It is important to note that Alembic *only* manages the structural schema. When a new column like `humidity` is added, historical rows default to `NULL`. To populate this column moving forward, the entire pipeline—from the Kafka Producer to the Silver ETL cleaner and API Pydantic schemas—must be updated in parallel during the same Pull Request.