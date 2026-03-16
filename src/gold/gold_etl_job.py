# Sandbox template gold layer etl jobb.
import psycopg
import logging
from src.config.db_config import get_dsn

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_DSN = get_dsn()

# Hårda affärsregler från verksamheten
# Dessa som consumer taggar med warning, critical eller None
MAINTENANCE_WARNING_HOURS = 4000.0
ENGINE_TEMP_WARNING_C = 101.0
RPM_MAX_NORMAL = 1600.0
VIBRATION_MAX_NORMAL = 10.0


# ============================================
# NOTERA: I GOLD SKRIVER VI INGA IF SATSER FÖR ATT RÄTTA STAVFEL, SMUTS ELLER NÅGOT. 
# HÄR FLYTTAS ENBART REN DATA TILL RENA TABLES.
# MÄRKER VI FEL I GOLDEN LAYER LIGGER PROBLEMET I SILVER. SANNOLIKT I TVÄTTEN!
# ============================================

def run_gold_etl():
    """Moves clean data from Silver, gets Surrogate Keys(SK) and BUILDS FACT-table"""
    # Hämta och connecta
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:

            # ==========
            # 1) DELTA LOAD: Hämtar enbart giltig data som INTE redan finns i GOLD
            # ==========
            cur.execute("""
                SELECT
                        silver_id, engine_id, appliance_type, timestamp,
                        run_hours, location, rpm, engine_temp, vibration_hz
                FROM silver_sensor_data
                WHERE is_valid = TRUE
                    AND silver_id NOT IN (SELECT silver_id FROM fact_sensor_reading);
            """)

            # Hämtar alla nya rader om det finns. Finns det ej får vi meddelande om det.
            # Finns nya rader meddelas vi om det med i terminal med antal nya rader
            new_rows = cur.fetchall()
            if not new_rows:
                logger.info(
                    "No new valid rows found in Silver. Gold is up to date!")

            logger.info(
                f"Found {len(new_rows)} new rows to process for Gold layer.")

            # Variabel för att hålla koll på och räkna antal processerade rader
            processed_count = 0

            for row in new_rows:
                (silver_id, engine_id, appliance_type, timestamp,
                 run_hours, location, rpm, engine_temp, vibration_hz) = row

                # ==========
                # 2) DIMENSION UPSERTS (Hämta SK för varje textsträng)
                # DO UPDATE SET uppdaterar med samma värde,
                # vilket tvingar Postgres att alltid RETURNERA vårt SK-ID!
                # ==========

                # Engine
                cur.execute("""
                    INSERT INTO dim_engine (engine_id) VALUES (%s)
                    ON CONFLICT (engine_id) DO UPDATE SET engine_id = EXCLUDED.engine_id
                    RETURNING engine_sk;
                """, (engine_id,))
                engine_sk = cur.fetchone()[0]

                # Location
                cur.execute("""
                    INSERT INTO dim_location (location) VALUES (%s)
                    ON CONFLICT (location) DO UPDATE SET location = EXCLUDED.location
                    RETURNING location_sk;
                """, (location,))
                location_sk = cur.fetchone()[0]

                # Appliance
                cur.execute("""
                    INSERT INTO dim_appliance (appliance_type) VALUES (%s)
                    ON CONFLICT (appliance_type) DO UPDATE SET appliance_type = EXCLUDED.appliance_type
                    RETURNING appliance_sk;
                """, (appliance_type,))
                appliance_sk = cur.fetchone()[0]

                # Date (Hämtar året, månad, och dag från timestamp)
                d_date = timestamp.date()
                cur.execute("""
                    INSERT INTO dim_date (calendar_date, year, month, day) 
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (calendar_date) DO UPDATE SET calendar_date = EXCLUDED.calendar_date
                    RETURNING date_sk;
                """, (d_date, d_date.year, d_date.month, d_date.day))
                date_sk = cur.fetchone()[0]

                # ==========
                # 3) AFFÄRSLOGIKEN
                # Beräknar alla larm på plats i GOLD
                # ==========
                maint_warn = bool(run_hours and run_hours >=
                                  MAINTENANCE_WARNING_HOURS)
                temp_warn = bool(engine_temp and engine_temp >=
                                 ENGINE_TEMP_WARNING_C)
                rpm_warn = bool(rpm and rpm > RPM_MAX_NORMAL)
                vibration_warn = bool(
                    vibration_hz and vibration_hz > VIBRATION_MAX_NORMAL)

                # ==========
                # 4) INSERT FACTS
                # ==========
                cur.execute("""
                    INSERT INTO fact_sensor_reading (
                        engine_sk, location_sk, date_sk, appliance_sk,
                        event_ts, run_hours, rpm, engine_temp, vibration_hz,
                        maintenance_warning, temp_warning, rpm_warning, vibration_warning,
                        silver_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    engine_sk, location_sk, date_sk, appliance_sk,
                    timestamp, run_hours, rpm, engine_temp, vibration_hz,
                    maint_warn, temp_warn, rpm_warn, vibration_warn,
                    silver_id
                ))

                processed_count += 1

            conn.commit()
            logger.info(
                f"Successfully processed {processed_count} rows and inserted into Gold fact Table!")


if __name__ == "__main__":
    run_gold_etl()
