# Script that reads from Kafka
import os
import json
import logging
import psycopg
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError, KafkaException
from pydantic import BaseModel, ValidationError, Field
from datetime import datetime
from typing import Optional

# Load environment variables
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5440")
DB_NAME = os.getenv("DB_NAME")
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Maintenance thresholds (from project spec)
MAINTENANCE_WARNING_HOURS = 4000
MAINTENANCE_CRITICAL_HOURS = 5000
ENGINE_TEMP_WARNING_C = 101.0
RPM_MAX_NORMAL = 1600.0
VIBRATION_MAX_NORMAL = 10.0


# --- 1. PYDANTIC VALIDATION MODEL ---
class SensorEvent(BaseModel):
    engine_id: str
    appliance_type: str
    timestamp: datetime
    run_hours: float = Field(..., ge=0.0, le=10500.0)
    location: str
    rpm: Optional[float] = Field(None, ge=0.0, le=5000.0)
    engine_temp: Optional[float] = Field(None, ge=10.0, le=150.0)
    vibration_hz: Optional[float] = Field(None, ge=0.0, le=50.0)


# --- 2. DATABASE SETUP ---
def setup_database() -> None:
    """Creates staging and dead letter queue tables if they don't exist."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            # Staging table: raw JSON preserved as TEXT so ETL/Pandas can clean it downstream.
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS staging_sensor_data (
                    id                 SERIAL PRIMARY KEY,
                    raw_data           TEXT NOT NULL,
                    maintenance_flag   TEXT,
                    temp_flag          TEXT,
                    rpm_flag           TEXT,
                    vibration_flag     TEXT,
                    ingested_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            # Dead Letter Queue: stores rejected events with the reason they failed validation.
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
                "Database ready: staging_sensor_data + faulty_events tables confirmed."
            )


# --- 3. FLAG LOGIC ---
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


# --- 4. KAFKA CONSUMER ---
def run_consumer(
    bootstrap_servers: str = "localhost:9092",
    group_id: str = "sensor-consumer-group",
    topic: str = "sensor_data_stream",
) -> None:
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }

    consumer = Consumer(conf)
    consumer.subscribe([topic])
    logger.info(f"Consumer subscribed to topic: '{topic}' | group: '{group_id}'")

    try:
        setup_database()

        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                logger.info("Starting QA gate. Press CTRL+C to stop.\n")

                while True:
                    msg = consumer.poll(timeout=1.0)
                    if msg is None:
                        continue
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        else:
                            raise KafkaException(msg.error())

                    # Capture the raw message before any parsing or validation
                    raw_json_string = msg.value().decode("utf-8")

                    try:
                        raw_dict = json.loads(raw_json_string)

                        # Pydantic validates in memory only — used for flag calculation, not for cleaning
                        event = SensorEvent(**raw_dict)

                        maintenance_flag = get_maintenance_flag(event.run_hours)
                        temp_flag = get_temp_flag(event.engine_temp)
                        rpm_flag = get_rpm_flag(event.rpm)
                        vibration_flag = get_vibration_flag(event.vibration_hz)

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

                        # Insert raw string into staging — dirt intentionally preserved for downstream ETL
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
                        logger.info(
                            f"PASSED: engine={event.engine_id} | type={event.appliance_type}"
                        )

                    except ValidationError as e:
                        # Pydantic rejected the event — route to dead letter queue
                        cur.execute(
                            "INSERT INTO faulty_events (raw_data, error_reason) VALUES (%s, %s)",
                            (raw_json_string, str(e)),
                        )
                        logger.warning(
                            f"REJECTED (validation): {str(e).splitlines()[0]}"
                        )

                    except (json.JSONDecodeError, Exception) as e:
                        # Malformed JSON or unexpected error — also goes to dead letter queue
                        cur.execute(
                            "INSERT INTO faulty_events (raw_data, error_reason) VALUES (%s, %s)",
                            (raw_json_string, str(e)),
                        )
                        logger.error(f"REJECTED (critical): {e}")

                    conn.commit()

    except KeyboardInterrupt:
        logger.info("Consumer stopped by user (Ctrl+C).")
    finally:
        consumer.close()
        logger.info("Consumer closed.")


if __name__ == "__main__":
    run_consumer()
