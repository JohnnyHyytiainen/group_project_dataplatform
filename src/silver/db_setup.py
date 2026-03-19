# skapa en table i silver lagret som är mer strukturerad och har strikta datatyper,
# samt en unik constraint för att undvika dubbletter och för att göra scriptet idempotent (kan köras flera gånger utan att skapa dubbletter eller krascha)
import os


import psycopg
from src.config.db_config import (
    get_dsn,
)  # Importera funktionen för att hämta DSN från vår config fil


# Hämta config DSN ifrån src/config/db_config.py
DB_DSN = get_dsn()


# Skapa kopplingen till databasen för att kunna skapa vår silver table
def create_silver_table():
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            # Skapa en table med strikta data types för vår ren data ur silver layer
            cur.execute("""
                CREATE TABLE IF NOT EXISTS silver_sensor_data (
                    silver_id SERIAL PRIMARY KEY,
                    engine_id TEXT,
                    appliance_type TEXT,
                    timestamp TIMESTAMP,
                    run_hours FLOAT,
                    location TEXT,
                    rpm FLOAT,
                    engine_temp FLOAT,
                    vibration_hz FLOAT,
                    is_valid BOOLEAN,
                    silver_processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE NULLS NOT DISTINCT (engine_id, timestamp) -- DENNA RAD ÄR KRITISK OCH GÖR SCRIPTET IDEMPOTENT(Kan köras flera gånger)
                );
            """)
            conn.commit()
            print("Silver table 'silver_sensor_data' is now created")


# ==========================
# LÄGG IN CHECKS AV CONSTRAINTS
# ==========================
if __name__ == "__main__":
    create_silver_table()
