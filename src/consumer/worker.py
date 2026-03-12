# Kafka consumer — Bronze layer ingestion (Medallion Architecture)
import json
import logging
import psycopg
from confluent_kafka import Consumer, KafkaError, KafkaException
from typing import Optional

from pydantic import ValidationError
from src.schemas.sensor_schema import SensorEvent
from src.config.db_config import get_dsn

# DB connection string built from .env (Separation of Concerns)
DB_DSN = get_dsn()

# Logging with timestamp and level prefix
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Business rule thresholds -> ALL_CAPS = constants, change in one place only
MAINTENANCE_WARNING_HOURS = 4000
MAINTENANCE_CRITICAL_HOURS = 5000
ENGINE_TEMP_WARNING_C = 101.0
RPM_MAX_NORMAL = 1600.0
VIBRATION_MAX_NORMAL = 10.0


# --- DATABASE SETUP ---
def setup_database() -> None:
    """Creates Bronze (staging) and Dead Letter Queue tables if they don't exist."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            # Bronze table: raw JSON stored as TEXT -> cleaning happens in Silver layer
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS staging_sensor_data (
                    id               SERIAL PRIMARY KEY,
                    raw_data         TEXT NOT NULL,
                    maintenance_flag TEXT,
                    temp_flag        TEXT,
                    rpm_flag         TEXT,
                    vibration_flag   TEXT,
                    ingested_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            # DLQ: stores events that failed JSON parsing entirely, with the reason
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS faulty_events (
                    id           SERIAL PRIMARY KEY,
                    raw_data     TEXT,
                    error_reason TEXT,
                    ingested_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            logger.info(
                "Database ready: staging_sensor_data + faulty_events confirmed."
            )


# --- FLAG LOGIC ---
# Each function checks one sensor value and returns WARNING, CRITICAL, or None
# Optional[float] = value can be a float or None (sensor offline)


def get_maintenance_flag(run_hours: float) -> Optional[str]:
    if run_hours >= MAINTENANCE_CRITICAL_HOURS:
        return "CRITICAL"
    elif run_hours >= MAINTENANCE_WARNING_HOURS:
        return "WARNING"
    return None


def get_temp_flag(engine_temp: Optional[float]) -> Optional[str]:
    if engine_temp is None:
        return None
    elif engine_temp >= ENGINE_TEMP_WARNING_C:
        return "WARNING"
    return None


def get_rpm_flag(rpm: Optional[float]) -> Optional[str]:
    if rpm is None:
        return None
    elif rpm > RPM_MAX_NORMAL:
        return "WARNING"
    return None


def get_vibration_flag(vibration_hz: Optional[float]) -> Optional[str]:
    if vibration_hz is None:
        return None
    elif vibration_hz > VIBRATION_MAX_NORMAL:
        return "WARNING"
    return None


# --- KAFKA CONSUMER ---
def run_consumer(
    bootstrap_servers: str = "localhost:19092",
    group_id: str = "sensor-consumer-group",
    topic: str = "sensor_data_stream",
) -> None:
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        # Manual commit: we control exactly when Kafka marks a message as processed
        "enable.auto.commit": False,
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic])
    logger.info(f"Subscribed to topic: '{topic}' | group: '{group_id}'")

    try:
        setup_database()

        # Single long-lived DB connection for the entire session
        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                logger.info("Bronze layer open. Press CTRL+C to stop.\n")

                while True:
                    msg = consumer.poll(timeout=1.0)

                    if msg is None:
                        # No message arrived within timeout -> keep waiting
                        continue
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # Reached end of partition -> not an error, keep going
                            continue
                        else:
                            raise KafkaException(msg.error())

                    # Decode raw bytes before any parsing — needed for DLQ if things go wrong
                    raw_json_string = msg.value().decode("utf-8")

                    try:
                        # Step 1: Parse JSON — if this fails, message is unreadable garbage
                        raw_dict = json.loads(raw_json_string)

                        # Step 2: Default flags to None —> ensures they exist even if Pydantic fails
                        maintenance_flag = None
                        temp_flag = None
                        rpm_flag = None
                        vibration_flag = None

                        # Step 3: Pydantic validation — isolated in its own try/except
                        # Pydantic is a WARNING SYSTEM here, not a gatekeeper
                        # A failure logs to faulty_events but does NOT stop Bronze ingestion
                        try:
                            event = SensorEvent(**raw_dict)

                            # Calculate flags from validated event
                            maintenance_flag = get_maintenance_flag(event.run_hours)
                            temp_flag = get_temp_flag(event.engine_temp)
                            rpm_flag = get_rpm_flag(event.rpm)
                            vibration_flag = get_vibration_flag(event.vibration_hz)

                            # Log any triggered flags in real time
                            if maintenance_flag:
                                logger.warning(
                                    f"[MAINTENANCE {maintenance_flag}] engine={event.engine_id} | run_hours={event.run_hours}h"
                                )
                            if temp_flag:
                                logger.warning(
                                    f"[TEMPERATURE {temp_flag}] engine={event.engine_id} | temp={event.engine_temp}°C"
                                )
                            if rpm_flag:
                                logger.warning(
                                    f"[RPM {rpm_flag}] engine={event.engine_id} | rpm={event.rpm}"
                                )
                            if vibration_flag:
                                logger.warning(
                                    f"[VIBRATION {vibration_flag}] engine={event.engine_id} | vibration={event.vibration_hz}hz"
                                )

                        except ValidationError as e:
                            # Pydantic rejected it (e.g. missing engine_id, format_noise)
                            # Record in faulty_events for tracking —> data still goes to Bronze
                            cur.execute(
                                "INSERT INTO faulty_events (raw_data, error_reason) VALUES (%s, %s)",
                                (raw_json_string, str(e)),
                            )
                            logger.warning(
                                f"PYDANTIC WARNING (still saving to Bronze): {str(e).splitlines()[0]}"
                            )

                        # Step 4: Always save to Bronze —> this is the Medallion architecture
                        # Raw JSON preserved as it is -> Silver layer handles all cleaning
                        cur.execute(
                            """
                            INSERT INTO staging_sensor_data
                                (raw_data, maintenance_flag, temp_flag, rpm_flag, vibration_flag)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                raw_json_string,
                                maintenance_flag,
                                temp_flag,
                                rpm_flag,
                                vibration_flag,
                            ),
                        )

                        engine_id_log = raw_dict.get("engine_id", "MISSING_ID")
                        logger.info(f"BRONZE: engine={engine_id_log}")

                    except json.JSONDecodeError as e:
                        # Completely unreadable message — only goes to DLQ, not Bronze
                        cur.execute(
                            "INSERT INTO faulty_events (raw_data, error_reason) VALUES (%s, %s)",
                            (raw_json_string, str(e)),
                        )
                        logger.error(f"REJECTED (malformed JSON): {e}")

                    except Exception as e:
                        # Unexpected error —> also goes to DLQ, logged as ERROR
                        cur.execute(
                            "INSERT INTO faulty_events (raw_data, error_reason) VALUES (%s, %s)",
                            (raw_json_string, str(e)),
                        )
                        logger.error(f"REJECTED (unexpected error): {e}")

                    # Commit DB first, then Kafka — if DB fails, Kafka redelivers the message
                    conn.commit()
                    consumer.commit(message=msg)

    except KeyboardInterrupt:
        logger.info("Consumer stopped by user (Ctrl+C).")
    finally:
        consumer.close()
        logger.info("Consumer closed.")


if __name__ == "__main__":
    run_consumer()
