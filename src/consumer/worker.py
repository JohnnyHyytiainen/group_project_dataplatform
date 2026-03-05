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
DB_PORT = os.getenv("DB_PORT", "5439")
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

# Engine temperature threshold — matches producer's extreme_temp fault at 101.0°C
ENGINE_TEMP_WARNING_C = 101.0

# RPM threshold — matches producer's normal range max of 1600
RPM_MAX_NORMAL = 1600.0

# Vibration threshold — matches producer's normal range max of 10hz
VIBRATION_MAX_NORMAL = 10.0


# --- 2. DATABASE SETUP ---
def setup_database() -> None:
    """Creates staging and dead letter queue tables if they don't exist."""
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            # Table for valid, clean sensor data
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS staging_sensor_data (
                    id                 SERIAL PRIMARY KEY,
                    engine_id          TEXT NOT NULL,
                    appliance_type     TEXT NOT NULL,
                    run_hours          FLOAT NOT NULL,
                    location           TEXT NOT NULL,
                    rpm                FLOAT,
                    engine_temp        FLOAT,
                    vibration_hz       FLOAT,
                    maintenance_flag   TEXT,
                    temp_flag          TEXT,
                    rpm_flag           TEXT,
                    vibration_flag     TEXT,
                    event_timestamp    TIMESTAMP NOT NULL,
                    ingested_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            # Dead Letter Queue — stores rejected events with reason
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS faulty_events (
                    id           SERIAL PRIMARY KEY,
                    raw_data     JSONB,
                    error_reason TEXT,
                    ingested_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )
            conn.commit()
            logger.info(
                "Database ready: staging_sensor_data + faulty_events tables confirmed."
            )


# --- 3. MAINTENANCE FLAG LOGIC ---
def get_maintenance_flag(run_hours: float) -> Optional[str]:
    """
    Returns a maintenance flag based on engine run hours.
    Warranty limit: 5000h. Flag warning at 4000h.
    """
    if run_hours >= MAINTENANCE_CRITICAL_HOURS:
        return "CRITICAL"
    elif run_hours >= MAINTENANCE_WARNING_HOURS:
        return "WARNING"
    return None


# --- 4. TEMPERATURE FLAG LOGIC ---
def get_temp_flag(engine_temp: Optional[float]) -> Optional[str]:
    """
    Returns a temperature flag if the engine is running too hot.
    Matches producer's extreme_temp fault threshold of 101.0°C.
    """
    if engine_temp is None:
        return None
    elif engine_temp >= ENGINE_TEMP_WARNING_C:
        return "WARNING"
    return None


# --- 5. RPM FLAG LOGIC ---
def get_rpm_flag(rpm: Optional[float]) -> Optional[str]:
    """
    Returns a flag if rpm exceeds the normal operating range.
    Matches producer's extreme_rpm fault threshold of 1601+.
    """
    if rpm is None:
        return None
    elif rpm > RPM_MAX_NORMAL:
        return "WARNING"
    return None


# --- 6. VIBRATION FLAG LOGIC ---
def get_vibration_flag(vibration_hz: Optional[float]) -> Optional[str]:
    """
    Returns a flag if vibration exceeds the normal operating range.
    Matches producer's extreme_vibration fault threshold of 11+hz.
    """
    if vibration_hz is None:
        return None
    elif vibration_hz > VIBRATION_MAX_NORMAL:
        return "WARNING"
    return None
