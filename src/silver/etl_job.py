import json
import psycopg
import os

from psycopg import dict_row

from src.silver.cleaner import clean_event

from src.config.db_config import get_dsn

# hämta db inställningar. Anropar funktionen som bygger anslutningssträngen.

DB_DSN = get_dsn()

PROCESSED_FIL = "data/processed/cleaned_sensor_data.jsonl"


def run_silver_batch():

    print(f"Starting the batch cleaning job for silver")

    os.makedirs(os.path.dirname(PROCESSED_FIL), exist_ok=True)

    with psycopg.connect(DB_DSN) as conn:

        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute("SELECT id, FROM_staging_sensor_data;")

            bronze_rows = cur.fetchall()
            if not bronze_rows:
                print("No data find in staging. Exiting!")

                return

            with open(PROCESSED_FIL, "a", encoding="utf-8") as processed_file:

                line_processed = 0

                for row in bronze_rows:

                    try:
                        raw_data = row["raw_data"]
                        if isinstance(raw_data, dict):
                            raw_dict = raw_data

                        else:
                            raw_dict = json.loads(raw_data)

                        clean_dict = clean_event(raw_dict)

                        cur.execute(
                            """
                                                                       
                                    INSERT INTO silver_sensor_data
                                    (engine_id, applience_type, timestamp, run_hours, location,
                                    rpm, engine_temp, vibration_hz, is_valid)
                                    VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (engine_id, timestamp) DO NOTHING
                                    RETURNING silver_id                            
                                    """,
                            (
                                clean_dict.get("engine_id"),
                                clean_dict.get("appliance_type"),
                                clean_dict.get("timestamp"),
                                clean_dict.get("run_hours"),
                                clean_dict.get("location"),
                                clean_dict.get("rpm"),
                                clean_dict.get("engine_temp"),
                                clean_dict.get("vibration_hz"),
                                clean_dict.get("is_valid"),
                            ),
                        )

                        inserted_row = cur.fetchone()

                        if inserted_row:
                            processed_file.write(json.dumps(clean_dict) + "\n")
                            line_processed += 1

                    except json.JSONDecodeError as e:
                        print("Skipping row {row['id']} due to invalid JSON: {e}")

                    except Exception as e:
                        print(f"Error processing row {row['id']}: {e}")

                conn.commit()

                print(
                    f"Work is done. {line_processed} Rows processed, cleaned and saved in Silver layer."
                )


if __name__ == "__main__":
    run_silver_batch()
