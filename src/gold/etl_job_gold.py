import psycopg
import logging

# Fix
# from src.config.db_config import get_dsn
from src.config.db_config import get_dsn

# Sätter upp grundinställningar för logging
# Fix — add return
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Skapar en logger
logger = logging.getLogger(__name__)

# Hämtar databasens connection string (DSN)
DB_DSN = get_dsn()

# Tröskelvärden för affärslogiken
MAINTENANCE_WARNING_HOURS = 4000.0
ENGINE_TEMP_WARNING_C = 101.0
RPM_MAX_NORMAL = 1600.0
VIBRATION_MAX_NORMAL = 10.0


def run_gold_etl():
    """Moves clean data from Silver, gets Surrogate Keys(SK) and BUILDS FACT-table"""

    # Öppnar anslutningen mot datgabases
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    silver_id,
                    engine_id,
                    appliance_type,
                    timestamp,
                    run_hours,
                    location,
                    rpm,
                    engine_temp,
                    vibration_hz
                FROM silver_sensor_data
                WHERE is_valid = TRUE
                    AND silver_id NOT IN
                        (SELECT silver_id FROM fact_sensor_reading);
            """
            )

            # Hämtar allar rader från SELECT-resultatet
            new_rows = cur.fetchall()

            # Om inga nya rader finns, logga och avsluta funktionen direkt
            if not new_rows:
                logger.info("No new valid rows found in Silver. Gold is up to date!")
                return

            # Loggar hur många nya rader som ska processas
            logger.info(f"Found {len(new_rows)} new rows to process for Gold layer.")

            # Variabel för att räkna hur många rader som processats
            processed_count = 0

            for row in new_rows:
                try:
                    # Försöker processa en rad i taget så att varje rad blir en egen transaktion.
                    # Om allt lyckas för raden ska den committas.

                    (
                        silver_id,
                        engine_id,
                        appliance_type,
                        timestamp,
                        run_hours,
                        location,
                        rpm,
                        engine_temp,
                        vibration_hz,
                    ) = row

                    # Ser  till att motorn finns i dimensionstabellen,
                    # hämta dess surrogate key, och använd den i fact-tabellen
                    cur.execute(
                        """
                                INSERT INTO dim_engine (engine_id) 
                                VALUES (%s)
                                ON CONFLICT (engine_id)
                                DO UPDATE SET 
                                    engine_id = EXCLUDED.engine_id
                                RETURNING engine_sk;
                                """,
                        (engine_id,),
                    )
                    engine_sk = cur.fetchone()[0]

                    # Säkerställer att location finns i dim_location,
                    # hämtar location_sk och använder location_sk i fact-tabellen
                    cur.execute(
                        """
                            
                            INSERT INTO dim_location (location) 
                            VALUES (%s)
                            ON CONFLICT (location)
                            DO UPDATE SET
                                location = EXCLUDED.location
                            RETURNING location_sk;
                            """,
                        (location,),
                    )
                    location_sk = cur.fetchone()[0]

                    # Lägger in appliance_type om den saknas,
                    # annars används den som redan finns och hämta appliance_sk
                    cur.execute(
                        """                            
                            INSERT INTO dim_appliance (appliance_type) 
                            VALUES (%s)
                            ON CONFLICT (appliance_type)
                            DO UPDATE SET
                                appliance_type = EXCLUDED.appliance_type
                            RETURNING appliance_sk;
                            """,
                        (appliance_type,),
                    )
                    appliance_sk = cur.fetchone()[0]

                    # Date (Hämtar året, månad, och dag från timestamp)
                    d_date = timestamp.date()

                    # Lägger in datumet i dim_date om det saknas,
                    # annars använd det som redan finns, och hämta date_sk
                    cur.execute(
                        """
                            
                            INSERT INTO dim_date (calendar_date, year, month, day)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (calendar_date)
                            DO UPDATE SET
                                calendar_date = EXCLUDED.calendar_date
                            RETURNING date_sk;
                                """,
                        (d_date, d_date.year, d_date.month, d_date.day),
                    )
                    date_sk = cur.fetchone()[0]

                    # Affärslogik, skapar warningsflaggor baserat på om
                    # mätvärdena passerar gränsvärdena
                    maint_warn = bool(
                        run_hours and (run_hours >= MAINTENANCE_WARNING_HOURS)
                    )

                    temp_warn = bool(
                        engine_temp and (engine_temp >= ENGINE_TEMP_WARNING_C)
                    )

                    rpm_warn = bool(rpm and (rpm > RPM_MAX_NORMAL))

                    vibration_warn = bool(
                        vibration_hz and (vibration_hz > VIBRATION_MAX_NORMAL)
                    )

                    # Sparar den färdiga, analysklara raden i fact_sensor_reading med surrogate keys,
                    # mätvärden och varningsflaggor och räknar upp antal processade rader.
                    cur.execute(
                        """
                        
                            INSERT INTO fact_sensor_reading (
                                engine_sk, location_sk, date_sk, appliance_sk,
                                event_ts, run_hours, rpm, engine_temp, vibration_hz,
                                maintenance_warning, temp_warning, rpm_warning, vibration_warning,
                                silver_id
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                        """,
                        (
                            engine_sk,
                            location_sk,
                            date_sk,
                            appliance_sk,
                            timestamp,
                            run_hours,
                            rpm,
                            engine_temp,
                            vibration_hz,
                            maint_warn,
                            temp_warn,
                            rpm_warn,
                            vibration_warn,
                            silver_id,
                        ),
                    )

                    processed_count += 1

                    # Sparar just denna rad permanent i databasen först när hela raden lyckats.
                    # Detta gör att varje rad commitas separat.
                    conn.commit()

                except psycopg.Error as e:
                    # Om ett databasfel sker (t.ex. constraint error eller SQL-fel),
                    # återställs hela transaktionen för just denna rad.
                    conn.rollback()
                    print(f"Database error on silver_id {silver_id}: {e}. Rolled back.")
                    # Fångar alla andra oväntade fel för raden.
                    # Rollback görs också här för att inte lämna transaktionen i ett trasigt läge.

                except Exception as e:
                    conn.rollback()
                    print(
                        f"Error processing row {silver_id}: {e}. Rolled∏ back attempted."
                    )

            logger.info(
                f"Successfully processed {processed_count} rows and inserted into Gold fact Table!"
            )


if __name__ == "__main__":
    run_gold_etl()
