import psycopg
import logging
from src.config.db_config import get_dsn

# loggning
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Hämta vår DSN
DB_DSN = get_dsn()

# Funktion för daily aggregation. Aggregerar data från fact_sensor_reading till fact_engine_daily.
# Idempotent script som kan köras hur många gånger som helst och kommer ENDAST uppdatera daily statistik med senaste siffrorna.


def run_daily_aggregation():
    """
    Aggregates data from fact_sensor_reading to fact_engine_daily.
    This script can be run any number of times (idempotent) and will
    only update today's statistics with the most recent numbers.
    """

    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            logger.info("Starting daily aggredation for dashboards")

            # Grupperar på Motor OCH Datum
            # ON CONFLICT == möjligt att köra om och om igen utan issues.
            # Uppdaterar ENBART siffrorna istället för att skapa dubbletter.
            cur.execute("""
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
                    MAX(engine_temp) AS max_engine_temp,
                    AVG(rpm) AS avg_rpm,
                    MAX(vibration_hz) AS max_vibration,
                    MAX(run_hours) AS max_run_hours,
                
                    -- Omvandlar True/False till 1/0 och summerar alla larm för dagen
                    SUM(
                        maintenance_warning::int +
                        temp_warning::int +
                        rpm_warning::int +
                        vibration_warning::int
                    ) AS warnings_total
                FROM fact_sensor_reading
                GROUP BY engine_sk, date_sk
                        
                -- Idempotens! Om raden redan finns för denna motor och detta datum, 
                -- uppdatera bara med de nya Max/Avg-värdena.
                ON CONFLICT (engine_sk, date_sk) DO UPDATE SET
                    max_engine_temp = EXCLUDED.max_engine_temp,
                    avg_rpm = EXCLUDED.avg_rpm,
                    max_vibration = EXCLUDED.max_vibration,
                    max_run_hours = EXCLUDED.max_run_hours,
                    warnings_total = EXCLUDED.warnings_total;
            """)

            # För att logga antal rader som påverkades
            affected_rows = cur.rowcount
            conn.commit()

            logger.info(
                f"Dashboard aggregation completed. {affected_rows} daily records UPSERT'ed"
            )


if __name__ == "__main__":
    run_daily_aggregation()
