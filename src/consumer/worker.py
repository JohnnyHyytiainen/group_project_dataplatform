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
