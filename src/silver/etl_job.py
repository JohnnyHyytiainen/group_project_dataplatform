import json
import psycopg
import os

from psycopg.rows import dict_row
from src.silver.cleaner import clean_event
from src.config.db_config import get_dsn

# Hämtar DB-inställningar genom att anropa funktionen som bygger anslutningssträngen.
DB_DSN = get_dsn()

# Sökväg till filen där vi sparar den tvättade datan från silver-lagret.
PROCESSED_FIL = "data/processed/cleaned_sensor_data.jsonl"


def run_silver_batch():
    """
    Process raw sensor events from the bronze staging table, clean and validate each record,
    insert valid rows into the silver table, and persist processed output to a JSONL file.
    """

    print("Starting the batch cleaning job for silver")
    os.makedirs(os.path.dirname(PROCESSED_FIL), exist_ok=True)

    # Öppnar databasanslutning och hämtar all rådata från bronze/staging-lagret.
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT id, raw_data FROM staging_sensor_data;")

            bronze_rows = cur.fetchall()
            if not bronze_rows:
                print("No data found in staging. Exiting!")

                return

            # Öppnar JSONL-filen i append-läge och initierar räknare för processade rader.
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

                        # Skriver tvättad data till silver-tabellen.
                        # Använder savepoint för att kunna rulla tillbaka trasiga delar av transaktionen
                        # ON CONFLICT skyddar mot dubletter om samma event körs igen.
                        with conn.transaction():
                            cur.execute(
                                """                                        
                            INSERT INTO silver_sensor_data
                            (engine_id, appliance_type, timestamp, run_hours, location,
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
                            # skriver till JSONL enbart om raden sattes in( inte var en dubblett)

                            if inserted_row:
                                processed_file.write(json.dumps(clean_dict) + "\n")
                                line_processed += 1

                    except json.JSONDecodeError as e:
                        print(f"Skipping row {row['id']} due to invalid JSON: {e}")

                    except psycopg.Error as e:

                        print(
                            f"Database error on row {row['id']}: {e}. Row safely rolled back."
                        )

                    except Exception as e:
                        print(f"Error processing row {row['id']}: {e}. Row skipped.")

                conn.commit()
                print(
                    f"Work is done. {line_processed} Rows processed, cleaned and saved in Silver layer."
                )


# Kör batch-jobbet endast om filen startas direkt.
if __name__ == "__main__":
    run_silver_batch()
