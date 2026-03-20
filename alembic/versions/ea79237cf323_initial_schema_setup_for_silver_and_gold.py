"""Initial schema setup for Silver and Gold

Revision ID: ea79237cf323
Revises:
Create Date: 2026-03-20 13:25:47.882813

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea79237cf323"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Skapa bronze-lagret
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging_sensor_data (
                id               SERIAL PRIMARY KEY,
                raw_data         TEXT NOT NULL,
                maintenance_status   TEXT,
                temperature_status   TEXT,
                rpm_status           TEXT,
                vibration_status     TEXT,
                ingested_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
    """)

    # 2. Skapa vår DLQ table
    op.execute("""
        CREATE TABLE IF NOT EXISTS faulty_events (
                id           SERIAL PRIMARY KEY,
                raw_data     TEXT,
                error_reason TEXT,
                ingested_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
    """)

    # 2. Skapa silver lagret
    op.execute("""
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
            UNIQUE NULLS NOT DISTINCT (engine_id, timestamp)
        );
    """)

    # 3. Skapa gold-layer (Dimensioner MÅSTE skapas innan Fakta)
    # Dimensioner
    op.execute("""
        CREATE TABLE IF NOT EXISTS dim_engine (
            engine_sk SERIAL PRIMARY KEY,
            engine_id TEXT UNIQUE NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS dim_location (
            location_sk SERIAL PRIMARY KEY,
            location TEXT UNIQUE NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS dim_date (
            date_sk SERIAL PRIMARY KEY,
            calendar_date DATE UNIQUE NOT NULL,
            year INT NOT NULL,
            month INT NOT NULL,
            day INT NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS dim_appliance (
            appliance_sk SERIAL PRIMARY KEY,
            appliance_type TEXT UNIQUE NOT NULL
        );
    """)

    # Fakta-tabeller (Kräver att dimensionerna och silver finns)
    op.execute("""
        CREATE TABLE IF NOT EXISTS fact_sensor_reading (
            reading_id BIGSERIAL PRIMARY KEY,
            
            -- Foreign Keys (FK)
            engine_sk INT REFERENCES dim_engine(engine_sk),
            location_sk INT REFERENCES dim_location(location_sk),
            date_sk INT REFERENCES dim_date(date_sk),
            appliance_sk INT REFERENCES dim_appliance(appliance_sk),
            
            event_ts TIMESTAMP NOT NULL,
            run_hours FLOAT,
            rpm FLOAT,
            engine_temp FLOAT,
            vibration_hz FLOAT,
            
            -- Kalkylerad logik från Gold ETL
            maintenance_warning BOOLEAN,
            temp_warning BOOLEAN,
            rpm_warning BOOLEAN,
            vibration_warning BOOLEAN,
            
            -- UK (Unique Key) & Spårbarhet till Silver
            silver_id INT UNIQUE REFERENCES silver_sensor_data(silver_id)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS fact_engine_daily (
            engine_daily_id BIGSERIAL PRIMARY KEY,
            
            -- Foreign Keys (FK)
            engine_sk INT REFERENCES dim_engine(engine_sk),
            date_sk INT REFERENCES dim_date(date_sk),
            
            -- Dagliga mätvärden
            max_engine_temp FLOAT,
            avg_rpm FLOAT,
            max_vibration FLOAT,
            max_run_hours FLOAT,
            warnings_total INT,
            
            UNIQUE (engine_sk, date_sk)
        );
    """)


def downgrade() -> None:
    # 1. Droppa Fakta-tabellerna (eftersom de är beroende av Dimensionerna) (Gold)
    op.execute("DROP TABLE IF EXISTS fact_engine_daily;")
    op.execute("DROP TABLE IF EXISTS fact_sensor_reading;")

    # 2. Droppa Dimensionerna (Gold)
    op.execute("DROP TABLE IF EXISTS dim_appliance;")
    op.execute("DROP TABLE IF EXISTS dim_date;")
    op.execute("DROP TABLE IF EXISTS dim_location;")
    op.execute("DROP TABLE IF EXISTS dim_engine;")

    # 3. Droppa Silver och Bronze lagret
    op.execute("DROP TABLE IF EXISTS silver_sensor_data;")
    op.execute("DROP TABLE IF EXISTS faulty_events;")
    op.execute("DROP TABLE IF EXISTS staging_sensor_data;")
