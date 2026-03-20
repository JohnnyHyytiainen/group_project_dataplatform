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
            # Create tables
            cur.execute("""
                CREATE TABLE IF NOT EXISTS daily_aggregation (
                    engine_id TEXT PRIMARY KEY,
                    max_temperature FLOAT,
                    average_rpm FLOAT
                );
            """)

            # Create aggregations and inserting them into the tables
            cur.execute(
                """
                INSERT INTO daily_aggregation (engine_id, max_temperature, average_rpm)
                SELECT 
                    engine_id,
                    round(max(engine_temp)::numeric, 1),
                    round(avg(rpm))
                FROM silver_sensor_data
                WHERE is_valid = TRUE
                GROUP BY engine_id
                RETURNING engine_id, max_temperature, average_rpm;
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
            print("Work is done. Aggregated and saved in Daily aggregation layer.")


if __name__ == "__main__":
    run_daily_aggregation()
