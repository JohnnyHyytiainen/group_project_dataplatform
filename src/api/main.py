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
    version="1.0",
)
# BEST PRACTICE: Variabel [lista med tillåtna URL'er som vi tillåter]

# 1) Middleware
# Gör det möjligt för framtida frontend (Streamlit, powerBI etc) att prata med API utan CORS blockage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # BEST PRACTICE == ÄNDRA -> Dashboard PORT.
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
    appliance_type: Optional[str] = None,
    is_valid: Optional[bool] = None,
    db: psycopg.Connection = Depends(get_db_connection),  # <-- Lånar från poolen!
):
    base_query = "SELECT * FROM silver_sensor_data WHERE 1=1"
    params: List[Any] = []

    if appliance_type is not None:
        base_query += " AND appliance_type = %s"
        params.append(appliance_type)

    if is_valid is not None:
        base_query += " AND is_valid = %s"
        params.append(is_valid)

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
                },
            },
            "data": rows,
        }
    except Exception as e:
        # NYTT: Istället för att krascha tyst loggar jag nu VAD felet är/var.
        # Visar klart och tydligt i terminal output vad som är fel. T.ex, 'appliance_type' saknas i DB etc.
        logger.error(f"Database query failed in /api/v1/sensors: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")
