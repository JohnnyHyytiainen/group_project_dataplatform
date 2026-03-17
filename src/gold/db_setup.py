# Importera mina deps
import psycopg
import logging   # För att kunna logga vad som händer i scriptet, vilket är
from src.config.db_config import get_dsn # Importera funktionen för att hämta DSN från vår config fil

# Logging funktioner.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Hämta database 'Data Source Name'
DB_DSN = get_dsn()


# Setup av gold layer tables
def setup_gold_layer():
    """
    Creating Dimensions tables and Fact tables for golden layer.
    Based on gold layer ERD.
    """

    with psycopg.connect(DB_DSN) as conn: # Skapa en connection till databasen, och använd 'with' så att den stängs automatiskt när vi är klara
        with conn.cursor() as cur:
            
            logger.info("Creating Dimension tables...")
            
            # DIM_ENGINE table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_engine (
                    engine_sk SERIAL PRIMARY KEY,
                    engine_id TEXT UNIQUE NOT NULL
                );
            """)
            
            # DIM_LOCATION table 
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_location (
                    location_sk SERIAL PRIMARY KEY,
                    location TEXT UNIQUE NOT NULL
                );
            """)
            
            # DIM_DATE table 
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_date (
                    date_sk SERIAL PRIMARY KEY,
                    calendar_date DATE UNIQUE NOT NULL,
                    year INT NOT NULL,
                    month INT NOT NULL,
                    day INT NOT NULL
                );
            """)

            # DIM_APPLIANCE table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dim_appliance (
                    appliance_sk SERIAL PRIMARY KEY,
                    appliance_type TEXT UNIQUE NOT NULL
                );
            """)

            logger.info("Creating Fact tables...")
            
            # FACT_SENSOR_READING (Huvudfaktan, hjärtat i gold_layer_PDM.png / gold_layer_PDM.mmd)
            cur.execute("""
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

            # FACT_ENGINE_DAILY (Aggregerad fakta för Dashboards)
            cur.execute("""
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
                    
                    -- Vi lägger in en UNIQUE constraint här så att vi inte råkar
                    -- skapa flera rader för samma motor och dag om skriptet körs två gånger
                    UNIQUE (engine_sk, date_sk)
                );
            """)
            
            conn.commit()
            logger.info("Gold Layer tables created successfully exactly matching ERD!")

if __name__ == "__main__":
    setup_gold_layer()