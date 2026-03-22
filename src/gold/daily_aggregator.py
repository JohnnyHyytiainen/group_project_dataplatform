import json
import psycopg
from psycopg.rows import dict_row
from src.config.db_config import get_dsn
import os

# Hämtar DB-inställningar genom att anropa funktionen som bygger anslutningssträngen.
DB_DSN = get_dsn()

# Sökväg till filen där vi sparar den tvättade datan från silver-lagret.
PROCESSED_FILE = "data/processed/daily_aggregation.jsonl"


def run_daily_aggregation():

    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Create aggregations and inserting them into the tables
            cur.execute(
                """
                INSERT INTO fact_engine_daily (
                engine_sk,
                date_sk,
                max_engine_temp,
                avg_rpm,
                max_vibration,
                max_run_hours,
                warnings_total
                )
                SELECT
                    engine_sk,
                    date_sk,
                    ROUND(MAX(engine_temp)::numeric, 1) max_engine_temp,
                    ROUND(AVG(rpm)) avg_rpm,
                    ROUND(MAX(vibration_hz)::numeric, 1) max_vibration,
                    MAX(run_hours) max_run_hours,
                    SUM(
                        maintenance_warning::int +
                        temp_warning::int +
                        rpm_warning::int +
                        vibration_warning::int
                    ) warnings_total
                FROM fact_sensor_reading
                GROUP BY
                    engine_sk,
                    date_sk
                ORDER BY
                    engine_sk,
                    date_sk
                ON CONFLICT do nothing
                RETURNING *;
                """
            )

            inserted_rows = cur.fetchall()

            with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
                if not inserted_rows:
                    print("No data found.")
                    return

                for row in inserted_rows:
                    f.write(json.dumps(row) + "\n")

                print("Writing to:", os.path.abspath(PROCESSED_FILE))

            conn.commit()
            print(f"Work is done. Inserted {cur.rowcount} rows to fact_engine_daily.")


if __name__ == "__main__":
    run_daily_aggregation()
