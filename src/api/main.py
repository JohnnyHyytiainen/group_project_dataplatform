from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psycopg
from psycopg.rows import dict_row
from typing import Optional, List, Any
from datetime import datetime
import logging


# Importera  pool-logik
# Ännu en import behövs för att hämta pydantic schema när det är byggt
from src.api.database_connection_pool import (
    init_db_pool,
    close_db_pool,
    get_db_connection,
)
from src.schemas.api_schemas import PaginatedSensorResponse

# db_setup.py innehåller ej larm-flaggor (maintenance_flags etc)
# Logik byggs runt is_valid och appliance_type istället.

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Det här körs INNAN API't börjar ta emot calls
    init_db_pool()
    yield
    # Det här körs NÄR API't stängs av.
    close_db_pool()


app = FastAPI(
    title="IoT Appliance Sensor API",
    lifespan=lifespan,  # <-- Kopplar in vår pool!
    version="2.0",
)
# BEST PRACTICE: Variabel [lista med tillåtna URL'er som vi tillåter]
origins = ["http://localhost:8501"]

# 1) Middleware
# Gör det möjligt för framtida frontend (Streamlit, powerBI etc) att prata med API utan CORS blockage
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # BEST PRACTICE == ÄNDRA -> Dashboard PORT.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========
# ENDPOINTS
# ==========


# Standard framsida
@app.get("/")
def read_root():
    return {"Message": "Welcome to the IoT Sensor API. Visit /docs for documentation"}


# en /health enpoint. Kollar att DB är vid liv genom en enkel SELECT 1
@app.get("/health")
def health_check(db: psycopg.Connection = Depends(get_db_connection)):
    """
    Checks that BOTH API and DB is alive and healthy by doing a quick SELECT 1
    """
    try:
        with db.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
    }


# /api/v1/sensors endpoint. Pagination + filtering.
# Notera "response_model=PaginatedSensorResponse". Detta är sker i schemas/api_schemas.py
@app.get("/api/v1/sensors", response_model=PaginatedSensorResponse)
def get_sensor_data(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    appliance_type: Optional[str] = Query(
        None, description="Example: dishwasher, washing_machine or dryer"
    ),
    is_valid: Optional[bool] = Query(
        None, description="Filters entirely on CLEAN or FAULTY data"
    ),
    # --- Nya query parameters för att kunna filtrera ---
    engine_id: Optional[str] = Query(None, description="Search for SPECIFIC engine-ID"),
    location: Optional[str] = Query(
        None, description="Filter for which city the machine is in"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Retrieve data starting from this data"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Retrieve data until this date"
    ),
    # --- --- --- --- --- ---
    db: psycopg.Connection = Depends(
        get_db_connection
    ),  # <--- Lånar från connection pool
):

    # WHERE 1=1 är tricket som låter mig bygga allting dynamiskt
    base_query = "SELECT * FROM silver_sensor_data WHERE 1=1"
    params: List[Any] = []

    # 1) Existerande filter
    if appliance_type is not None:
        base_query += " AND appliance_type = %s"
        params.append(appliance_type)

    if is_valid is not None:
        base_query += " AND is_valid = %s"
        params.append(is_valid)

    # 2) Nya str filters
    if engine_id is not None:
        base_query += " AND engine_id = %s"
        params.append(engine_id)

    if location is not None:
        base_query += " AND location = %s"
        params.append(location)

    # 3) Nya tid/datum filter. Användbara för grafer
    if start_date is not None:
        base_query += " AND timestamp >= %s"
        params.append(start_date)

    if end_date is not None:
        base_query += " AND timestamp <= %s"
        params.append(end_date)

    # Avslutar med att alltid sortera på nyaste datan först, gäller även pagination(sidindelning)
    base_query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
    params.extend([limit, skip])

    try:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(base_query, params)
            rows = cur.fetchall()

        return {
            "metadata": {
                "total_returned": len(rows),
                "skip": skip,
                "limit": limit,
                "filters_applied": {
                    "appliance_type": appliance_type,
                    "is_valid": is_valid,
                    "engine_id": engine_id,
                    "location": location,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            },
            "data": rows,
        }
    except Exception as e:
        # Istället för att krascha TYST loggar jag nu VAD felet är/var.
        # Visar klart och tydligt i terminal output vad som är fel. T.ex 'appliance_type' saknas i DB etc.
        logger.error(f"Database query failed in /api/v1/sensors: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


# ENDPOINT FÖR GOLD LAYER
# Dashboard
@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(
    location: Optional[str] = Query(None),
    appliance_type: Optional[str] = Query(None),
    db: psycopg.Connection = Depends(get_db_connection),
):
    """Aggregated Gold data for dashboard cards and graphs"""
    query = """
        SELECT
            a.appliance_type,
            l.location,
            COUNT(DISTINCT e.engine_id)                          AS antal_motorer,
            ROUND(AVG(fsr.engine_temp)::numeric, 1)              AS snitt_temp,
            ROUND(AVG(fsr.run_hours)::numeric, 1)                AS snitt_drifttid,
            COUNT(*) FILTER (WHERE fsr.temp_warning)             AS överhettade,
            COUNT(*) FILTER (WHERE fsr.rpm_warning)              AS hög_rpm,
            COUNT(*) FILTER (WHERE fsr.vibration_warning)        AS hög_vibration,
            COUNT(*) FILTER (WHERE fsr.run_hours > 400
                AND (fsr.temp_warning OR fsr.rpm_warning
                     OR fsr.vibration_warning))                  AS dubbel_riskfaktor
        FROM fact_sensor_reading fsr
        JOIN dim_engine    e ON fsr.engine_sk    = e.engine_sk
        JOIN dim_appliance a ON fsr.appliance_sk = a.appliance_sk
        JOIN dim_location  l ON fsr.location_sk  = l.location_sk
        WHERE 1=1
    """
    params = []
    if location:
        query += " AND l.location = %s"
        params.append(location)
    if appliance_type:
        query += " AND a.appliance_type = %s"
        params.append(appliance_type)

    query += " GROUP BY a.appliance_type, l.location ORDER BY dubbel_riskfaktor DESC"

    try:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return {"data": cur.fetchall()}
    except Exception as e:
        logger.error(f"Dashboard summary query failed: {e}")
        raise HTTPException(status_code=500, detail="Query failed")
